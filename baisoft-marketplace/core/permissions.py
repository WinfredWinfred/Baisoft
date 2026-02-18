from rest_framework import permissions


class IsBusinessMember(permissions.BasePermission):
    """
    Permission to check if user is a member of the business.
    """
    
    message = "You do not have permission to access this resource."
    
    def has_permission(self, request, view):
        """Check if user is authenticated."""
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """Check if user belongs to the same business as the object."""
        if not request.user.is_authenticated:
            return False
        
        # Admin users can access anything
        if request.user.role == 'admin':
            return True
        
        # Check if user and object belong to the same business
        user_business = getattr(request.user, 'business', None)
        obj_business = getattr(obj, 'business', None)
        
        return user_business == obj_business


class IsBusinessAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin in their business.
    Only business admins can manage users and roles in their business.
    """
    
    message = "Only business administrators can perform this action."
    
    def has_permission(self, request, view):
        """Check if user is an admin in their business."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        """Check if user is admin of the same business."""
        if not request.user.is_authenticated:
            return False
        
        # Check if user is admin
        if request.user.role != 'admin':
            return False
        
        # Check if managing user belongs to same business
        user_business = getattr(obj, 'business', None)
        return request.user.business == user_business


class CanApproveProduct(permissions.BasePermission):
    """
    Custom permission to only allow users with 'admin' or 'approver' role
    to approve products.
    """
    
    message = "Only users with admin or approver role can approve products."
    
    def has_permission(self, request, view):
        """Check if user has permission to approve products."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'approver']
    
    def has_object_permission(self, request, view, obj):
        """Check if user can approve this specific product."""
        if not request.user.is_authenticated:
            return False
        
        # Check if user belongs to the same business
        if request.user.business != obj.business:
            return False
        
        return request.user.role in ['admin', 'approver']


class CanManageProduct(permissions.BasePermission):
    """
    Custom permission to allow users with 'admin' or 'editor' role
    to create or edit products.
    """
    
    message = "Only users with admin or editor role can manage products."
    
    def has_permission(self, request, view):
        """Check if user has permission to manage products."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'editor']
    
    def has_object_permission(self, request, view, obj):
        """
        Check if user has permission to edit/delete a specific product.
        Allow admins to manage any product in their business, editors to manage their own.
        """
        if not request.user.is_authenticated:
            return False
        
        # Check if user belongs to the same business
        if request.user.business != obj.business:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'editor':
            return obj.created_by == request.user
        
        return False
