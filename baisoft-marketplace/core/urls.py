from django.urls import path
from core import views

app_name = 'core'

urlpatterns = [
    # Auth endpoints
    path('auth/me/', views.CurrentUserAPIView.as_view(), name='current-user'),
    
    # Business endpoints
    path('business/me/', views.BusinessDetailView.as_view(), name='business-detail'),
    path('business/users/', views.BusinessUsersListCreateView.as_view(), name='business-users'),
    path('business/users/<int:pk>/', views.BusinessUserDetailView.as_view(), name='business-user-detail'),
    
    # Public products endpoint
    path('products/public/', views.PublicProductsListView.as_view(), name='public-products'),
    
    # Internal products endpoints (authenticated)
    path('products/internal/', views.InternalProductsListCreateView.as_view(), name='internal-products'),
    
    # Product detail endpoints (retrieve, update, delete)
    path('products/<int:pk>/', views.ProductUpdateDeleteView.as_view(), name='product-detail'),
    
    # Approve product endpoint
    path('products/<int:pk>/approve/', views.ApproveProductAPIView.as_view(), name='approve-product'),
    
    # Bulk approve products endpoint
    path('products/bulk-approve/', views.BulkApproveProductsAPIView.as_view(), name='bulk-approve-products'),
]
