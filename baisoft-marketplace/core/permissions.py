from rest_framework import permissions


class IsBusinessMember(permissions.BasePermission):
    """Check if user is a member of the business."""
    
    message = "You do not have permission to access this resource."
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
            return True
        
        user_business = getattr(request.user, 'business', None)
        obj_business = getattr(obj, 'business', None)
        
        return user_business == obj_business


class IsBusinessAdmin(permissions.BasePermission):
    """Check if user is an admin in their business."""
    
    message = "Only business administrators can perform this action."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role == 'admin'
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role != 'admin':
            return False
        
        user_business = getattr(obj, 'business', None)
        return request.user.business == user_business


class CanApproveProduct(permissions.BasePermission):
    """Allow users with admin or approver role to approve products."""
    
    message = "Only users with admin or approver role can approve products."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'approver']
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.business != obj.business:
            return False
        
        return request.user.role in ['admin', 'approver']


class CanViewProducts(permissions.BasePermission):
    """Allow users to view products based on role."""
    
    message = "You do not have permission to view internal products."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return request.user.role in ['admin', 'editor', 'approver']
        
        return request.user.role in ['admin', 'editor']


class CanManageProduct(permissions.BasePermission):
    """Allow users with admin or editor role to manage products."""
    
    message = "Only users with admin or editor role can manage products."
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        return request.user.role in ['admin', 'editor']
    
    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False
        
        if request.user.business != obj.business:
            return False
        
        if request.user.role == 'admin':
            return True
        
        if request.user.role == 'editor':
            return obj.created_by == request.user
        
        return False
