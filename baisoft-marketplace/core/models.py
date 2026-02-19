from django.db import models
from django.contrib.auth.models import AbstractUser


class Business(models.Model):
    """Business/Organization model that users belong to."""
    
    name = models.CharField(
        max_length=255,
        unique=True,
        help_text='Business name'
    )
    description = models.TextField(
        blank=True,
        help_text='Business description'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Business creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Business last update timestamp'
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Businesses'
    
    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom User model with roles and business association."""
    
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
        blank=True,
        help_text='Business this user belongs to'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        help_text='User role within the business'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this user account is active'
    )
    
    class Meta:
        ordering = ['-date_joined']
        unique_together = [['username', 'business']]
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def has_permission(self, action: str) -> bool:
        """
        Check if user has permission for a specific action.
        Actions: create_product, edit_product, delete_product, approve_product
        """
        if self.role == 'admin':
            return True
        
        action_permissions = {
            'create_product': ['admin', 'editor'],
            'edit_product': ['admin', 'editor'],
            'delete_product': ['admin'],
            'approve_product': ['admin', 'approver'],
            'view_all_products': ['admin', 'editor', 'approver'],
        }
        
        return self.role in action_permissions.get(action, [])


class Product(models.Model):
    """Product model with approval workflow and audit trail."""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
    ]
    
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='products',
        null=True,
        blank=True,
        help_text='Business this product belongs to'
    )
    name = models.CharField(
        max_length=255,
        help_text='Product name'
    )
    description = models.TextField(
        help_text='Product description'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Product price'
    )
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True,
        help_text='Product image'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Product approval status'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='products',
        help_text='User who created the product'
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='approved_products',
        null=True,
        blank=True,
        help_text='User who approved the product'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when product was approved'
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text='Soft delete flag'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when product was deleted'
    )
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='deleted_products',
        null=True,
        blank=True,
        help_text='User who deleted the product'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='Product creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Product last update timestamp'
    )
    
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
        """
        Validate status transitions based on current status and user role.
        
        Rules:
        - Draft can transition to pending_approval or approved
        - Pending_approval can transition to approved or back to draft
        - Approved can only be changed back by admin
        - Only admin/approver can set status to approved
        """
        # Admin can do anything
        if user.role == 'admin':
            return True
        
        # Can't unapprove a product unless admin
        if self.status == 'approved' and new_status != 'approved':
            return False
        
        # Only admin/approver can approve
        if new_status == 'approved' and user.role not in ['admin', 'approver']:
            return False
        
        # Editor can move between draft and pending_approval
        if user.role == 'editor':
            return new_status in ['draft', 'pending_approval']
        
        return True
    
    def soft_delete(self, user):
        """Soft delete the product."""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
    
    def restore(self):
        """Restore a soft-deleted product."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()
