from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from core.models import Product, User, Business
from core.serializers import ProductSerializer, UserSerializer, UserManagementSerializer, BusinessSerializer
from core.permissions import CanApproveProduct, CanManageProduct, CanViewProducts, IsBusinessAdmin


class PublicProductsListView(generics.ListAPIView):
    """Public endpoint for approved products."""
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Product.objects.select_related('business', 'created_by', 'approved_by').filter(
            status='approved', 
            is_deleted=False
        )


class InternalProductsListCreateView(generics.ListCreateAPIView):
    """Internal endpoint for managing products."""
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewProducts]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'name', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Product.objects.filter(business=self.request.user.business, is_deleted=False)
    
    def perform_create(self, serializer):
        if not self.request.user.business:
            raise PermissionError("You must be assigned to a business to create products.")
        
        status = self.request.data.get('status', 'draft')
        
        # Editors can only set draft or pending_approval
        if self.request.user.role == 'editor':
            if status not in ['draft', 'pending_approval']:
                status = 'draft'
        
        serializer.save(
            created_by=self.request.user,
            business=self.request.user.business,
            status=status
        )
    
    def create(self, request, *args, **kwargs):
        if not CanManageProduct().has_permission(request, self):
            return Response(
                {'detail': 'Only admin or editor users can create products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not request.user.business:
            return Response(
                {'detail': 'You must be assigned to a business to create products.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


class ProductUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Endpoint to retrieve, update, or delete a product."""
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageProduct]
    
    def get_queryset(self):
        if not self.request.user.business:
            return Product.objects.none()
        return Product.objects.filter(business=self.request.user.business, is_deleted=False)
    
    def get_object(self):
        obj = super().get_object()
        
        if obj.business != self.request.user.business:
            self.permission_denied(
                self.request,
                message="This product does not belong to your business."
            )
        
        return obj
    
    def check_object_permissions(self, request, obj):
        if request.user.role == 'admin':
            return
        
        if request.user.role == 'editor':
            if obj.created_by != request.user:
                self.permission_denied(
                    request,
                    message="You can only edit or delete your own products."
                )
        else:
            self.permission_denied(
                request,
                message="Only admin or editor users can manage products."
            )
    
    def perform_update(self, serializer):
        new_status = serializer.validated_data.get('status')
        instance = self.get_object()
        
        # Validate status transition
        if new_status and new_status != instance.status:
            if not instance.can_transition_to(new_status, self.request.user):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    f"You cannot change product status from {instance.status} to {new_status}."
                )
        
        # Editors can only set draft or pending_approval
        if self.request.user.role == 'editor':
            if new_status and new_status not in ['draft', 'pending_approval']:
                serializer.validated_data.pop('status', None)
        
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.role != 'admin' and instance.created_by != request.user:
            return Response(
                {'detail': 'You can only delete your own products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Soft delete
        instance.soft_delete(request.user)
        
        return Response(
            {'detail': 'Product deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ApproveProductAPIView(APIView):
    """Endpoint to approve a product."""
    
    permission_classes = [permissions.IsAuthenticated, CanApproveProduct]
    
    def post(self, request, pk):
        from django.utils import timezone
        
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not CanApproveProduct().has_permission(request, self):
            return Response(
                {'detail': 'Only admin or approver users can approve products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if product.business != request.user.business:
            return Response(
                {'detail': 'This product does not belong to your business.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if product.status == 'approved':
            return Response(
                {'detail': 'This product is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve with audit trail
        product.status = 'approved'
        product.approved_by = request.user
        product.approved_at = timezone.now()
        product.save()
        
        serializer = ProductSerializer(product, context={'request': request})
        return Response(
            {
                'detail': 'Product approved successfully and is now visible to the public.',
                'product': serializer.data
            },
            status=status.HTTP_200_OK
        )


class CurrentUserAPIView(APIView):
    """
    GET endpoint to retrieve current authenticated user information.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Return current user information."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class BusinessUsersListCreateView(generics.ListCreateAPIView):
    """
    API endpoint for managing users within a business.
    - GET: List all users in user's business
    - POST: Create a new user in user's business (admin only)
    
    Only business admins can create/manage users.
    
    Filtering & Search:
    - ?role=admin - Filter by role (admin, editor, approver, viewer)
    - ?is_active=true - Filter by active status
    - ?search=<term> - Search by username or email
    - ?ordering=-date_joined - Order by field (prefix - for descending)
    
    Pagination:
    - ?page=1 - Page number (10 items per page)
    """
    
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessAdmin]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email']
    ordering_fields = ['date_joined', 'username', 'role']
    ordering = ['-date_joined']
    
    def get_queryset(self):
        """Return users in the current user's business."""
        if not self.request.user.is_authenticated:
            return User.objects.none()
        
        return User.objects.filter(business=self.request.user.business)
    
    def perform_create(self, serializer):
        """Create user and assign to current user's business."""
        serializer.save(business=self.request.user.business)


class BusinessUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint for managing a specific user in a business.
    - GET: Retrieve user details
    - PUT/PATCH: Update user role/permissions (admin only)
    - DELETE: Remove user from business (admin only)
    
    Only the user's own business admin can manage them.
    """
    
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsBusinessAdmin]
    
    def get_queryset(self):
        """Return users in the current user's business."""
        if not self.request.user.is_authenticated:
            return User.objects.none()
        
        return User.objects.filter(business=self.request.user.business)


class BusinessDetailView(generics.RetrieveAPIView):
    """
    API endpoint to view business information.
    Each authenticated user can view their own business.
    """
    
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return current user's business."""
        if not self.request.user.business:
            self.permission_denied(
                self.request,
                message="You are not assigned to any business."
            )
        return self.request.user.business




class BulkApproveProductsAPIView(APIView):
    """
    POST endpoint to approve multiple products at once.
    
    Product Rules:
    - Only users with 'admin' or 'approver' role can bulk approve products
    - All products must belong to user's business
    - Only products in 'draft' or 'pending_approval' status will be approved
    - Returns summary of approved, skipped, and failed products
    - Maximum 100 products per request for security
    """
    
    permission_classes = [permissions.IsAuthenticated, CanApproveProduct]
    
    def post(self, request):
        """Approve multiple products in a single request."""
        from django.utils import timezone
        
        # Get product IDs from request
        product_ids = request.data.get('product_ids', [])
        
        if not product_ids:
            return Response(
                {'detail': 'No product IDs provided.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not isinstance(product_ids, list):
            return Response(
                {'detail': 'product_ids must be a list.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Security: Limit bulk operations to prevent abuse
        if len(product_ids) > 100:
            return Response(
                {'detail': 'Maximum 100 products can be approved at once.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate all IDs are integers
        try:
            product_ids = [int(pid) for pid in product_ids]
        except (ValueError, TypeError):
            return Response(
                {'detail': 'All product IDs must be valid integers.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify user has permission to approve
        if not CanApproveProduct().has_permission(request, self):
            return Response(
                {'detail': 'Only admin or approver users can approve products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get products that belong to user's business
        products = Product.objects.filter(
            id__in=product_ids,
            business=request.user.business,
            is_deleted=False
        )
        
        approved_count = 0
        skipped_count = 0
        failed_products = []
        approved_products = []
        
        for product in products:
            # Skip already approved products
            if product.status == 'approved':
                skipped_count += 1
                continue
            
            try:
                # Approve the product
                product.status = 'approved'
                product.approved_by = request.user
                product.approved_at = timezone.now()
                product.save()
                
                approved_count += 1
                approved_products.append(product.id)
            except Exception as e:
                failed_products.append({
                    'id': product.id,
                    'name': product.name,
                    'error': str(e)
                })
        
        # Calculate products not found
        found_ids = [p.id for p in products]
        not_found_ids = [pid for pid in product_ids if pid not in found_ids]
        
        return Response(
            {
                'detail': f'Bulk approval completed. {approved_count} approved, {skipped_count} skipped.',
                'summary': {
                    'total_requested': len(product_ids),
                    'approved': approved_count,
                    'skipped': skipped_count,
                    'failed': len(failed_products),
                    'not_found': len(not_found_ids)
                },
                'approved_product_ids': approved_products,
                'failed_products': failed_products,
                'not_found_ids': not_found_ids
            },
            status=status.HTTP_200_OK
        )


class RoleBasedThrottle:
    """
    Custom throttle class that applies different rate limits based on user role.
    """
    from rest_framework.throttling import UserRateThrottle
    
    class AdminThrottle(UserRateThrottle):
        rate = '10000/hour'
    
    class EditorThrottle(UserRateThrottle):
        rate = '1000/hour'
    
    class ApproverThrottle(UserRateThrottle):
        rate = '1000/hour'
    
    class ViewerThrottle(UserRateThrottle):
        rate = '500/hour'
