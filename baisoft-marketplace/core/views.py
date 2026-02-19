from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from core.models import Product, User, Business
from core.serializers import ProductSerializer, UserSerializer, UserManagementSerializer, BusinessSerializer
from core.permissions import CanApproveProduct, CanManageProduct, CanViewProducts, IsBusinessAdmin


class PublicProductsListView(generics.ListAPIView):
    """
    Public endpoint for listing approved products.
    Anyone can access (no authentication required).
    Only returns products with status='approved'.
    
    Filtering & Search:
    - ?search=<term> - Search by name or description
    - ?ordering=-created_at - Order by field (prefix - for descending)
    
    Pagination:
    - ?page=1 - Page number (10 items per page)
    """
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only approved and non-deleted products."""
        return Product.objects.filter(status='approved', is_deleted=False)


class InternalProductsListCreateView(generics.ListCreateAPIView):
    """
    Authenticated endpoint for managing products within a business.
    - GET: List all products in user's business (admin, editor, approver)
    - POST: Create new product (requires admin or editor role)
    
    Product Rules:
    - Admin, Editor, and Approver can view all products
    - Only Admin and Editor can create products
    - Products start in 'draft' status
    - Products belong to user's business
    
    Filtering & Search:
    - ?status=draft - Filter by status (draft, pending_approval, approved)
    - ?search=<term> - Search by name or description
    - ?ordering=-created_at - Order by field (prefix - for descending)
    
    Pagination:
    - ?page=1 - Page number (10 items per page)
    """
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, CanViewProducts]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'price', 'name', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return only products belonging to the current user's business (excluding soft-deleted)."""
        return Product.objects.filter(business=self.request.user.business, is_deleted=False)
    
    def perform_create(self, serializer):
        """Create product and assign to current user's business."""
        if not self.request.user.business:
            raise PermissionError("You must be assigned to a business to create products.")
        
        # Get status from request, default to draft
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
        """Override create to provide better error handling."""
        # Check authorization
        if not CanManageProduct().has_permission(request, self):
            return Response(
                {'detail': 'Only admin or editor users can create products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check business assignment
        if not request.user.business:
            return Response(
                {'detail': 'You must be assigned to a business to create products.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


class ProductUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    Authenticated endpoint to retrieve, update, or delete a product.
    
    Product Rules:
    - Users can only edit/delete their own products or all products if admin
    - Products must belong to user's business
    - Editors cannot change product status (only admins can)
    - Unauthorized actions are blocked with 403 Forbidden
    """
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, CanManageProduct]
    
    def get_queryset(self):
        """Return products in the current user's business."""
        if not self.request.user.business:
            return Product.objects.none()
        return Product.objects.filter(business=self.request.user.business)
    
    def get_object(self):
        """Get product and verify user has permission to access it."""
        obj = super().get_object()
        
        # Verify product belongs to user's business
        if obj.business != self.request.user.business:
            self.permission_denied(
                self.request,
                message="This product does not belong to your business."
            )
        
        return obj
    
    def check_object_permissions(self, request, obj):
        """Enforce authorization rules for product operations."""
        # Super admin users can manage any product in their business
        if request.user.role == 'admin':
            return
        
        # Editors can only manage their own products
        if request.user.role == 'editor':
            if obj.created_by != request.user:
                self.permission_denied(
                    request,
                    message="You can only edit or delete your own products."
                )
        else:
            # Other roles cannot manage products
            self.permission_denied(
                request,
                message="Only admin or editor users can manage products."
            )
    
    def perform_update(self, serializer):
        """Update product while maintaining authorization rules and status transition validation."""
        # Get the status from validated data
        new_status = serializer.validated_data.get('status')
        instance = self.get_object()
        
        # Validate status transition if status is being changed
        if new_status and new_status != instance.status:
            if not instance.can_transition_to(new_status, self.request.user):
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied(
                    f"You cannot change product status from {instance.status} to {new_status}."
                )
        
        # Editors can only set draft or pending_approval status
        if self.request.user.role == 'editor':
            if new_status and new_status not in ['draft', 'pending_approval']:
                # Remove status from update if editor tried to set it to approved
                serializer.validated_data.pop('status', None)
        
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """Soft delete product with authorization check."""
        instance = self.get_object()
        
        # Only admins or the creator can delete
        if request.user.role != 'admin' and instance.created_by != request.user:
            return Response(
                {'detail': 'You can only delete your own products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Perform soft delete instead of hard delete
        instance.soft_delete(request.user)
        
        return Response(
            {'detail': 'Product deleted successfully.'},
            status=status.HTTP_204_NO_CONTENT
        )


class ApproveProductAPIView(APIView):
    """
    POST endpoint to approve a product.
    
    Product Rules:
    - Only users with 'admin' or 'approver' role can approve products
    - Product must belong to user's business
    - Product must be in 'pending_approval' or 'draft' status
    - Unauthorized approval attempts are blocked with 403 Forbidden
    """
    
    permission_classes = [permissions.IsAuthenticated, CanApproveProduct]
    
    def post(self, request, pk):
        """Approve a product and make it visible to public."""
        
        # Get product and verify it exists
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response(
                {'detail': 'Product not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify user has permission to approve
        if not CanApproveProduct().has_permission(request, self):
            return Response(
                {'detail': 'Only admin or approver users can approve products.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify product belongs to user's business
        if product.business != request.user.business:
            return Response(
                {'detail': 'This product does not belong to your business.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify product is in a status that can be approved
        if product.status == 'approved':
            return Response(
                {'detail': 'This product is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Approve the product
        product.status = 'approved'
        product.save()
        
        serializer = ProductSerializer(product)
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

