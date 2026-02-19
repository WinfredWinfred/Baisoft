from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.models import User, Product, Business, ChatConversation, ChatMessage


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


class SimpleUserSerializer(serializers.ModelSerializer):
    """Simple user serializer without nested business."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Full user serializer with business."""
    
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'business_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class UserManagementSerializer(serializers.ModelSerializer):
    """Serializer for User management."""
    
    business_name = serializers.CharField(source='business.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'is_active', 'business_name']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id': {'read_only': True},
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class ProductSerializer(serializers.ModelSerializer):
    """Product serializer with audit fields."""
    
    created_by_username = serializers.SerializerMethodField()
    business_name = serializers.SerializerMethodField()
    approved_by_username = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'image', 'image_url', 'status',
            'business_name', 'created_by_username', 'approved_by_username', 'approved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_by_username', 'business_name', 'approved_by_username', 'approved_at',
            'created_at', 'updated_at'
        ]
    
    def get_created_by_username(self, obj):
        try:
            return obj.created_by.username if obj.created_by else 'Unknown'
        except:
            return 'Unknown'
    
    def get_business_name(self, obj):
        try:
            return obj.business.name if obj.business else 'No Business'
        except:
            return 'No Business'
    
    def get_approved_by_username(self, obj):
        try:
            return obj.approved_by.username if obj.approved_by else None
        except:
            return None
    
    def get_image_url(self, obj):
        try:
            if obj.image:
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return obj.image.url
        except:
            pass
        return None
    
    def validate_image(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError('Image file size cannot exceed 5MB.')
            
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
            if hasattr(value, 'content_type') and value.content_type not in allowed_types:
                raise serializers.ValidationError('Invalid image type. Allowed: JPEG, PNG, GIF, WebP.')
        
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'user_message', 'ai_response', 'created_at']
        read_only_fields = ['id', 'ai_response', 'created_at']


class ChatConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = ChatConversation
        fields = ['id', 'session_id', 'messages', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
