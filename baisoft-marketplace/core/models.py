from django.db import models
from django.contrib.auth.models import AbstractUser


class Business(models.Model):
    """Business/Organization model."""
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Businesses'
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with roles and business."""
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('editor', 'Editor'),
        ('approver', 'Approver'),
        ('viewer', 'Viewer'),
    ]
    
    business = models.ForeignKey(
        Business,
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
        blank=True
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer'
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-date_joined']
        unique_together = [['username', 'business']]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_permission(self, action: str) -> bool:
        """Check if user has permission for a specific action."""
        if self.role == 'admin':
            return True
        
        permissions = {
            'create_product': ['admin', 'editor'],
            'edit_product': ['admin', 'editor'],
            'delete_product': ['admin'],
            'approve_product': ['admin', 'approver'],
            'view_all_products': ['admin', 'editor', 'approver'],
        }
        
        return self.role in permissions.get(action, [])


class Product(models.Model):
    """Product model with approval workflow."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='products')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='approved_products', null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='deleted_products', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_by']),
            models.Index(fields=['business']),
            models.Index(fields=['is_deleted']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def can_transition_to(self, new_status, user):
        """Validate status transitions based on user role."""
        if user.role == 'admin':
            return True
        
        # Can't unapprove unless admin
        if self.status == 'approved' and new_status != 'approved':
            return False
        
        # Only admin/approver can approve
        if new_status == 'approved' and user.role not in ['admin', 'approver']:
            return False
        
        # Editor can move between draft and pending
        if user.role == 'editor':
            return new_status in ['draft', 'pending_approval']
        
        return True
    
    def soft_delete(self, user):
        """Mark product as deleted."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def restore(self):
        """Restore deleted product."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
