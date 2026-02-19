"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenRefreshView
from core.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


def health_check(request):
    return JsonResponse({"status": "ok", "message": "Baisoft Marketplace API is running"})


def seed_data(request):
    """One-time endpoint to seed test data"""
    from django.core.management import call_command
    try:
        call_command('seed_testdata')
        return JsonResponse({"status": "success", "message": "Test data seeded successfully"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def debug_cors(request):
    """Debug endpoint to check CORS settings"""
    from django.conf import settings
    return JsonResponse({
        "CORS_ALLOWED_ORIGINS": list(settings.CORS_ALLOWED_ORIGINS) if hasattr(settings, 'CORS_ALLOWED_ORIGINS') else [],
        "CORS_ALLOW_ALL_ORIGINS": settings.CORS_ALLOW_ALL_ORIGINS if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS') else False,
        "CORS_ALLOW_CREDENTIALS": settings.CORS_ALLOW_CREDENTIALS if hasattr(settings, 'CORS_ALLOW_CREDENTIALS') else False,
        "DEBUG": settings.DEBUG,
        "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
    })


urlpatterns = [
    path('', health_check, name='health'),
    path('seed/', seed_data, name='seed'),
    path('debug-cors/', debug_cors, name='debug-cors'),
    path('admin/', admin.site.urls),
    
    # JWT Authentication endpoints
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Core API routes
    path('api/', include('core.urls')),
]
