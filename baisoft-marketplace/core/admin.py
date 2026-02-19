from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Business, User, Product, ChatConversation, ChatMessage


# ===============================
# BUSINESS ADMIN
# ===============================
@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "user_count", "product_count")
    search_fields = ("name",)
    readonly_fields = ("created_at", "updated_at")

    def user_count(self, obj):
        return obj.users.count()

    user_count.short_description = "Users"

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = "Products"


# ===============================
# USER ADMIN
# ===============================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "email", "business", "role", "is_active", "is_staff")
    list_filter = ("role", "business", "is_active")
    search_fields = ("username", "email", "business__name")

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal Info", {"fields": ("first_name", "last_name", "email")}),
        ("Business & Role", {"fields": ("business", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important Dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "email",
                    "password1",
                    "password2",
                    "business",
                    "role",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )


# ===============================
# PRODUCT ADMIN
# ===============================
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "business",
        "price",
        "status_badge",
        "created_by",
        "approved_by",
        "is_deleted",
        "created_at",
    )
    list_filter = ("status", "business", "is_deleted")
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at", "approved_by", "approved_at", "deleted_by", "deleted_at", "created_by")

    def get_fieldsets(self, request, obj=None):
        if obj:
            return (
                ("Product Info", {"fields": ("name", "description", "price", "image")}),
                ("Business & Creator", {"fields": ("business", "created_by")}),
                ("Workflow", {"fields": ("status",)}),
                ("Audit Trail", {"fields": ("created_at", "updated_at", "approved_by", "approved_at")}),
                ("Soft Delete", {"fields": ("is_deleted", "deleted_by", "deleted_at")}),
            )
        else:
            return (
                ("Product Info", {"fields": ("name", "description", "price", "image")}),
                ("Business", {"fields": ("business",)}),
            )

    def status_badge(self, obj):
        colors = {
            "draft": "gray",
            "pending_approval": "orange",
            "approved": "green",
        }
        return format_html(
            '<b style="color:{};">{}</b>',
            colors.get(obj.status, "black"),
            obj.get_status_display(),
        )

    status_badge.short_description = "Status"

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
            if not obj.business and request.user.business:
                obj.business = request.user.business

        super().save_model(request, obj, form, change)



@admin.register(ChatConversation)
class ChatConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_id', 'message_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'user')
    search_fields = ('session_id', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    
    def message_count(self, obj):
        return obj.messages.count()
    
    message_count.short_description = 'Messages'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user_message_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user_message', 'ai_response')
    readonly_fields = ('created_at',)
    
    def user_message_preview(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    
    user_message_preview.short_description = 'User Message'
