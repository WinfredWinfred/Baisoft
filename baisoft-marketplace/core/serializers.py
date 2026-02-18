from rest_framework import serializers
from core.models import User, Product, Business


class BusinessSerializer(serializers.ModelSerializer):
    """Serializer for Business model."""
    
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Business
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'user_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """Get count of users in the business."""
        return obj.users.count()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (read-only)."""
    
    business = BusinessSerializer(read_only=True)
    business_id = serializers.PrimaryKeyRelatedField(
        queryset=Business.objects.all(),
        write_only=True,
        required=False,
        source='business'
    )
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'business', 'business_id', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for User management (create/update)."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'is_active']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True},
        }
    
    def create(self, validated_data):
        """Create a new user with encrypted password."""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with optional password change."""
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with read-only created_by."""
    
    created_by = UserSerializer(read_only=True)
    business = BusinessSerializer(read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'status',
            'business',
            'created_by',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'business', 'created_at', 'updated_at']
