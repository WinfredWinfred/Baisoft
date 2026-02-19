from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import User, Product, Business


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer to include user role and business info in token."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['role'] = user.role
        token['user_id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        
        if user.business:
            token['business_id'] = user.business.id
            token['business_name'] = user.business.name
        
        return token


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
    """Serializer for Product model with read-only created_by and audit fields."""
    
    created_by = UserSerializer(read_only=True)
    business = BusinessSerializer(read_only=True)
    approved_by = UserSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'description',
            'price',
            'image',
            'image_url',
            'status',
            'business',
            'created_by',
            'approved_by',
            'approved_at',
            'is_deleted',
            'deleted_by',
            'deleted_at',
            'created_at',
            'updated_at'
        ]
        read_only_fields = [
            'id', 
            'created_by', 
            'business', 
            'approved_by', 
            'approved_at',
            'is_deleted',
            'deleted_by',
            'deleted_at',
            'created_at', 
            'updated_at'
        ]
    
    def get_image_url(self, obj):
        """Get full URL for product image."""
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
