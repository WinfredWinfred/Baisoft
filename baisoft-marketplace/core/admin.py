from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count
from .models import User, Product, Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    """Admin for Business model with enhanced functionality."""
    list_display = ('name', 'user_count_display', 'product_count', 'active_editors', 'created_at_display')
    list_filter = ('created_at', 'users__role')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at', 'user_count_display', 'product_count', 'user_list')
    fieldsets = (
        ('Business Information', {'fields': ('name', 'description')}),
        ('Statistics', {'fields': ('user_count_display', 'product_count', 'user_list')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        """Optimize queryset with counts."""
        queryset = super().get_queryset(request)
        return queryset.annotate(
            user_count=Count('users', distinct=True),
            product_count=Count('products', distinct=True)
        )
    
    def user_count_display(self, obj):
        """Display number of users in business with colored badge."""
        count = obj.user_count if hasattr(obj, 'user_count') else obj.users.count()
        return format_html(
            '<span style="background-color: #417690; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            count
        )
    user_count_display.short_description = 'Users'
    
    def product_count(self, obj):
        """Display number of products in business."""
        count = obj.product_count if hasattr(obj, 'product_count') else obj.products.count()
        if count == 0:
            color = '#999'
        elif count < 5:
            color = '#f0ad4e'
        else:
            color = '#5cb85c'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, count
        )
    product_count.short_description = 'Products'
    
    def active_editors(self, obj):
        """Display number of active editors."""
        count = obj.users.filter(role__in=['admin', 'editor'], is_active=True).count()
        return format_html(
            '<span style="padding: 3px 8px; border-radius: 3px;">{} active</span>',
            count
        )
    active_editors.short_description = 'Active Editors'
    
    def created_at_display(self, obj):
        """Display formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    
    def user_list(self, obj):
        """Display list of users in business."""
        users = obj.users.all()
        if not users:
            return "No users assigned"
        user_html = '<ul style="margin: 0; padding-left: 20px;">'
        for user in users:
            role_colors = {
                'admin': '#d9534f',
                'editor': '#0275d8',
                'approver': '#5cb85c',
                'viewer': '#999',
            }
            color = role_colors.get(user.role, '#999')
            status = '✓' if user.is_active else '✗'
            user_html += f'<li>{user.username} <span style="color: {color}; font-weight: bold;">[{user.role}]</span> {status}</li>'
        user_html += '</ul>'
        return format_html(user_html)
    user_list.short_description = 'Users'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for custom User model with enhanced functionality."""
    list_display = ('username', 'email_display', 'business_display', 'role_display', 'permissions_display', 'status_display', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'business', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'business__name')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Business & Role', {'fields': ('business', 'role')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Note: Role-based permissions are enforced through the "role" field. Object-level permissions are enforced in the API layer.'
        }),
        ('Timestamps', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'business', 'role', 'is_active'),
        }),
    )
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    
    def email_display(self, obj):
        """Display email with truncation."""
        return obj.email if obj.email else '—'
    email_display.short_description = 'Email'
    
    def business_display(self, obj):
        """Display business with colored background."""
        if not obj.business:
            return format_html('<span style="color: #999;">Unassigned</span>')
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 6px; border-radius: 3px;">{}</span>',
            obj.business.name
        )
    business_display.short_description = 'Business'
    
    def role_display(self, obj):
        """Display role with color coding."""
        role_colors = {
            'admin': '#d9534f',
            'editor': '#0275d8',
            'approver': '#5cb85c',
            'viewer': '#999',
        }
        color = role_colors.get(obj.role, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_role_display()
        )
    role_display.short_description = 'Role'
    
    def permissions_display(self, obj):
        """Display object-level permissions summary."""
        permissions = []
        if obj.role == 'admin':
            permissions = ['Can create products', 'Can approve products', 'Can manage users', 'Can manage business']
        elif obj.role == 'editor':
            permissions = ['Can create products', 'Can edit own products']
        elif obj.role == 'approver':
            permissions = ['Can approve products']
        elif obj.role == 'viewer':
            permissions = ['Can view products']
        
        if not obj.is_active:
            permissions = ['ACCESS DISABLED']
            color = '#d9534f'
        else:
            color = '#5cb85c'
        
        return format_html(
            '<span style="color: {}; font-size: 11px;">{}</span>',
            color, ', '.join(permissions) if permissions else 'No permissions'
        )
    permissions_display.short_description = 'Object Permissions'
    
    def status_display(self, obj):
        """Display user status."""
        if obj.is_active:
            return format_html('<span style="color: #5cb85c; font-weight: bold;">●</span> Active')
        else:
            return format_html('<span style="color: #d9534f; font-weight: bold;">●</span> Inactive')
    status_display.short_description = 'Status'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model with enhanced functionality."""
    list_display = ('name_display', 'business_display', 'price_display', 'status_display', 'created_by_display', 'created_at_display', 'approval_status')
    list_filter = ('status', 'business', 'created_by__role', 'created_at')
    search_fields = ('name', 'description', 'business__name', 'created_by__username')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'creator_full_info', 'approval_info')
    fieldsets = (
        ('Product Information', {'fields': ('name', 'description', 'price')}),
        ('Business & Creator', {'fields': ('business', 'created_by', 'creator_full_info')}),
        ('Status', {'fields': ('status', 'approval_info')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    ordering = ('-created_at',)
    actions = ['approve_products', 'mark_as_draft', 'mark_as_pending']
    
    def name_display(self, obj):
        """Display product name with link."""
        return format_html('<strong>{}</strong>', obj.name)
    name_display.short_description = 'Product Name'
    
    def business_display(self, obj):
        """Display business name."""
        return format_html(
            '<span style="background-color: #e3f2fd; padding: 3px 6px; border-radius: 3px;">{}</span>',
            obj.business.name if obj.business else 'N/A'
        )
    business_display.short_description = 'Business'
    
    def price_display(self, obj):
        """Display price formatted."""
        return format_html('${:.2f}', obj.price)
    price_display.short_description = 'Price'
    
    def status_display(self, obj):
        """Display status with color coding."""
        status_colors = {
            'draft': '#ffc107',
            'pending_approval': '#0275d8',
            'approved': '#28a745',
        }
        color = status_colors.get(obj.status, '#999')
        status_text = obj.get_status_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, status_text
        )
    status_display.short_description = 'Status'
    
    def created_by_display(self, obj):
        """Display creator with role."""
        role_emoji = {'admin': '👑', 'editor': '✏️', 'approver': '✓', 'viewer': '👁️'}
        emoji = role_emoji.get(obj.created_by.role, '•')
        return format_html(
            '{} {} <span style="color: #999;">({})</span>',
            emoji, obj.created_by.username, obj.created_by.get_role_display()
        )
    created_by_display.short_description = 'Creator'
    
    def created_at_display(self, obj):
        """Display formatted creation date."""
        return obj.created_at.strftime('%Y-%m-%d')
    created_at_display.short_description = 'Created'
    
    def approval_status(self, obj):
        """Show quick approval status indicator."""
        if obj.status == 'approved':
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Approved</span>')
        elif obj.status == 'pending_approval':
            return format_html('<span style="color: #0275d8; font-weight: bold;">⏳ Pending</span>')
        else:
            return format_html('<span style="color: #999;">Draft</span>')
    approval_status.short_description = 'Approval'
    
    def creator_full_info(self, obj):
        """Display detailed creator information."""
        return format_html(
            '<div style="padding: 10px; background-color: #f5f5f5; border-radius: 4px;">'
            '<strong>Username:</strong> {}<br>'
            '<strong>Email:</strong> {}<br>'
            '<strong>Role:</strong> {}<br>'
            '<strong>Status:</strong> {}'
            '</div>',
            obj.created_by.username,
            obj.created_by.email or 'N/A',
            obj.created_by.get_role_display(),
            '✓ Active' if obj.created_by.is_active else '✗ Inactive'
        )
    creator_full_info.short_description = 'Creator Info'
    
    def approval_info(self, obj):
        """Display approval workflow information."""
        info = f'<strong>Current Status:</strong> {obj.get_status_display()}<br>'
        if obj.status == 'draft':
            info += '<span style="color: #666;">Next step: Submit for approval</span>'
        elif obj.status == 'pending_approval':
            info += '<span style="color: #0275d8;">Waiting for admin/approver to review</span>'
        else:
            info += '<span style="color: #28a745;">Product is public and visible to all users</span>'
        return format_html(f'<div style="padding: 8px; background-color: #f9f9f9; border-left: 3px solid #ddd; border-radius: 2px;">{info}</div>')
    approval_info.short_description = 'Approval Info'
    
    def approve_products(self, request, queryset):
        """Bulk approve selected products."""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} product(s) approved successfully.')
    approve_products.short_description = 'Approve selected products'
    
    def mark_as_draft(self, request, queryset):
        """Bulk mark selected products as draft."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} product(s) marked as draft.')
    mark_as_draft.short_description = 'Mark selected as draft'
    
    def mark_as_pending(self, request, queryset):
        """Bulk mark selected products as pending approval."""
        updated = queryset.update(status='pending_approval')
        self.message_user(request, f'{updated} product(s) marked as pending approval.')
    mark_as_pending.short_description = 'Mark selected as pending approval'
    
    def save_model(self, request, obj, form, change):
        """Set created_by to current user on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
