from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from core.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that includes user role and business info in the token."""
    serializer_class = CustomTokenObtainPairSerializer


def api_root(request):
    """Root endpoint providing API information."""
    return JsonResponse({
        "message": "Baisoft Marketplace API",
        "version": "1.0",
        "endpoints": {
            "auth": "/api/auth/login/",
            "products": "/api/products/public/",
            "admin": "/admin/"
        }
    })


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/', include('core.urls')),
]
