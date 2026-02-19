from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenRefreshView
from core.serializers import CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


def api_root(request):
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

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug endpoints
    from django.http import JsonResponse
    from core.models import Product
    from django.db import connection
    
    def debug_products(request):
        try:
            products = Product.objects.all()
            return JsonResponse({
                'total': products.count(),
                'approved': products.filter(status='approved').count(),
                'with_created_by': products.exclude(created_by__isnull=True).count(),
                'sample': list(products.values('id', 'name', 'status', 'created_by_id')[:5])
            })
        except Exception as e:
            return JsonResponse({'error': str(e), 'type': type(e).__name__}, status=500)
    
    def debug_schema(request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(core_product)")
                columns = cursor.fetchall()
                return JsonResponse({
                    'columns': [{'name': col[1], 'type': col[2], 'notnull': col[3], 'default': col[4]} for col in columns]
                })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    urlpatterns.append(path('debug/products/', debug_products))
    urlpatterns.append(path('debug/schema/', debug_schema))
