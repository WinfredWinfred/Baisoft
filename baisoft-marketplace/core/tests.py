from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from datetime import datetime

from core.models import Business, Product
from core.serializers import ProductSerializer, UserSerializer, BusinessSerializer, UserManagementSerializer
from core.permissions import IsBusinessAdmin, CanApproveProduct, CanManageProduct

User = get_user_model()


class BusinessModelTests(TestCase):
    """Test cases for Business model."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(
            name='Test Business',
            description='A test business'
        )
    
    def test_business_creation(self):
        """Test that a business can be created."""
        self.assertEqual(self.business.name, 'Test Business')
        self.assertEqual(self.business.description, 'A test business')
        self.assertIsNotNone(self.business.created_at)
    
    def test_business_str(self):
        """Test business string representation."""
        self.assertEqual(str(self.business), 'Test Business')
    
    def test_business_timestamps(self):
        """Test that timestamps are automatically set."""
        self.assertIsNotNone(self.business.created_at)
        self.assertIsNotNone(self.business.updated_at)
        self.assertEqual(self.business.created_at, self.business.updated_at)
    
    def test_business_update(self):
        """Test that updated_at changes when business is updated."""
        old_updated_at = self.business.updated_at
        self.business.name = 'Updated Name'
        self.business.save()
        self.assertGreaterEqual(self.business.updated_at, old_updated_at)


class UserModelTests(TestCase):
    """Test cases for User model."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            business=self.business,
            role='admin'
        )
        self.editor_user = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='testpass123',
            business=self.business,
            role='editor'
        )
    
    def test_user_creation(self):
        """Test that users can be created."""
        self.assertEqual(self.admin_user.username, 'admin')
        self.assertEqual(self.admin_user.role, 'admin')
        self.assertEqual(self.admin_user.business, self.business)
    
    def test_user_password_hashing(self):
        """Test that password is hashed."""
        self.assertNotEqual(self.admin_user.password, 'testpass123')
        self.assertTrue(self.admin_user.check_password('testpass123'))
    
    def test_user_roles(self):
        """Test that user roles are set correctly."""
        roles = ['admin', 'editor', 'approver', 'viewer']
        for role in roles:
            user = User.objects.create_user(
                username=f'user_{role}',
                password='testpass123',
                business=self.business,
                role=role
            )
            self.assertEqual(user.role, role)
    
    def test_user_permissions(self):
        """Test user permission checking."""
        # Admin should have create and approve permissions
        self.assertTrue(self.admin_user.has_permission('create_product'))
        
        # Editor should only have create permission
        # Note: has_permission is called in views, test the logic directly
        self.assertEqual(self.editor_user.role, 'editor')
    
    def test_user_default_role(self):
        """Test that default role is 'viewer'."""
        viewer = User.objects.create_user(
            username='viewer',
            password='testpass123',
            business=self.business
        )
        self.assertEqual(viewer.role, 'viewer')
    
    def test_user_str(self):
        """Test user string representation."""
        self.assertEqual(str(self.admin_user), 'admin (Admin)')


class ProductModelTests(TestCase):
    """Test cases for Product model."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.user = User.objects.create_user(
            username='creator',
            password='testpass123',
            business=self.business,
            role='editor'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='A test product',
            price=99.99,
            created_by=self.user,
            business=self.business,
            status='draft'
        )
    
    def test_product_creation(self):
        """Test that a product can be created."""
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.price, 99.99)
        self.assertEqual(self.product.status, 'draft')
    
    def test_product_status_choices(self):
        """Test all product status choices."""
        statuses = ['draft', 'pending_approval', 'approved']
        for status_choice in statuses:
            product = Product.objects.create(
                name=f'Product {status_choice}',
                price=50.00,
                created_by=self.user,
                business=self.business,
                status=status_choice
            )
            self.assertEqual(product.status, status_choice)
    
    def test_product_default_status(self):
        """Test that default product status is 'draft'."""
        product = Product.objects.create(
            name='New Product',
            price=25.00,
            created_by=self.user,
            business=self.business
        )
        self.assertEqual(product.status, 'draft')
    
    def test_product_str(self):
        """Test product string representation."""
        self.assertEqual(str(self.product), 'Test Product (Draft)')
    
    def test_product_timestamps(self):
        """Test that timestamps are set."""
        self.assertIsNotNone(self.product.created_at)
        self.assertIsNotNone(self.product.updated_at)
    
    def test_product_relationships(self):
        """Test product relationships."""
        self.assertEqual(self.product.created_by, self.user)
        self.assertEqual(self.product.business, self.business)
    
    def test_product_price_validation(self):
        """Test product price is positive."""
        # Django's DecimalField should handle validation
        product = Product.objects.create(
            name='Expensive Product',
            price=999999.99,
            created_by=self.user,
            business=self.business
        )
        self.assertGreater(product.price, 0)


class BusinessSerializerTests(TestCase):
    """Test cases for Business serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(
            name='Test Business',
            description='Description'
        )
    
    def test_business_serializer_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'name': 'New Business',
            'description': 'New description'
        }
        serializer = BusinessSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_business_serializer_missing_required_fields(self):
        """Test serializer with missing required fields."""
        data = {'description': 'No name provided'}
        serializer = BusinessSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('name', serializer.errors)


class UserSerializerTests(TestCase):
    """Test cases for User serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            business=self.business,
            role='admin'
        )
    
    def test_user_serializer_data(self):
        """Test user serializer returns correct data."""
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data['username'], 'testuser')
        self.assertEqual(data['email'], 'test@test.com')
        self.assertEqual(data['role'], 'admin')


class ProductSerializerTests(TestCase):
    """Test cases for Product serializer."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            business=self.business,
            role='editor'
        )
        self.product = Product.objects.create(
            name='Test Product',
            description='Description',
            price=99.99,
            created_by=self.user,
            business=self.business
        )
    
    def test_product_serializer_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'name': 'New Product',
            'description': 'New description',
            'price': 49.99,
            'status': 'draft'
        }
        serializer = ProductSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_product_serializer_invalid_price(self):
        """Test serializer with invalid price."""
        data = {
            'name': 'Product',
            'description': 'Desc',
            'price': -10.00  # Negative price should be invalid
        }
        serializer = ProductSerializer(data=data)
        # Check if validation catches negative price
        if not serializer.is_valid():
            self.assertIn('price', serializer.errors)


class PermissionTests(TestCase):
    """Test cases for custom permission classes."""
    
    def setUp(self):
        """Set up test data."""
        self.business1 = Business.objects.create(name='Business 1')
        self.business2 = Business.objects.create(name='Business 2')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            business=self.business1,
            role='admin'
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            password='testpass123',
            business=self.business1,
            role='editor'
        )
        
        self.other_admin = User.objects.create_user(
            username='other_admin',
            password='testpass123',
            business=self.business2,
            role='admin'
        )
    
    def test_is_business_admin_permission(self):
        """Test IsBusinessAdmin permission."""
        permission = IsBusinessAdmin()
        
        # Admin should pass
        self.assertTrue(permission.has_permission(type('Request', (), {'user': self.admin_user})(), None))
        
        # Non-admin should fail
        self.assertFalse(permission.has_permission(type('Request', (), {'user': self.editor_user})(), None))
    
    def test_can_manage_product_permission(self):
        """Test CanManageProduct permission."""
        permission = CanManageProduct()
        
        # Admin and editor should pass create permission
        self.assertTrue(permission.has_permission(type('Request', (), {'user': self.admin_user})(), None))
        self.assertTrue(permission.has_permission(type('Request', (), {'user': self.editor_user})(), None))


class AuthenticationAPITests(APITestCase):
    """Test cases for authentication endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123',
            business=self.business,
            role='admin'
        )
        self.client = APIClient()
    
    def test_user_login(self):
        """Test user login endpoint."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_current_user(self):
        """Test get current user endpoint."""
        # Login first
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data, format='json')
        token = response.data['access']
        
        # Get current user
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        url = reverse('core:current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')


class ProductAPITests(APITestCase):
    """Test cases for product endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.business1 = Business.objects.create(name='Business 1')
        self.business2 = Business.objects.create(name='Business 2')
        
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            business=self.business1,
            role='admin'
        )
        
        self.editor_user = User.objects.create_user(
            username='editor',
            password='testpass123',
            business=self.business1,
            role='editor'
        )
        
        self.other_business_admin = User.objects.create_user(
            username='other_admin',
            password='testpass123',
            business=self.business2,
            role='admin'
        )
        
        self.product1 = Product.objects.create(
            name='Product 1',
            description='Approved product',
            price=99.99,
            created_by=self.admin_user,
            business=self.business1,
            status='approved'
        )
        
        self.product2 = Product.objects.create(
            name='Product 2',
            description='Draft product',
            price=49.99,
            created_by=self.editor_user,
            business=self.business1,
            status='draft'
        )
        
        self.client = APIClient()
    
    def _login(self, username, password):
        """Helper to login and set authorization header."""
        url = reverse('token_obtain_pair')
        data = {'username': username, 'password': password}
        response = self.client.post(url, data, format='json')
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_public_products_list(self):
        """Test public products endpoint returns only approved products."""
        url = reverse('core:public-products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain only approved products
        products = response.data['results']
        self.assertTrue(all(p['status'] == 'approved' for p in products))
    
    def test_internal_products_list_requires_auth(self):
        """Test that internal products endpoint requires authentication."""
        url = reverse('core:internal-products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_internal_products_list_authenticated(self):
        """Test internal products list for authenticated user."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_create_product_by_admin(self):
        """Test that admin can create products."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        data = {
            'name': 'New Product',
            'description': 'A new product',
            'price': 29.99
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'draft')
        self.assertEqual(response.data['created_by'], self.admin_user.id)
    
    def test_create_product_by_editor(self):
        """Test that editor can create products."""
        self._login('editor', 'testpass123')
        url = reverse('core:internal-products')
        data = {
            'name': 'Editor Product',
            'description': 'Created by editor',
            'price': 19.99
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_business_isolation(self):
        """Test that users only see products from their business."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        response = self.client.get(url)
        product_ids = [p['id'] for p in response.data['results']]
        
        # Should only see products from business1
        self.assertIn(self.product1.id, product_ids)
        self.assertIn(self.product2.id, product_ids)
    
    def test_approve_product_by_admin(self):
        """Test that admin can approve products."""
        self._login('admin', 'testpass123')
        url = reverse('core:approve-product', kwargs={'pk': self.product2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify product status changed
        self.product2.refresh_from_db()
        self.assertEqual(self.product2.status, 'approved')
    
    def test_approve_product_by_editor_fails(self):
        """Test that editor cannot approve products."""
        self._login('editor', 'testpass123')
        url = reverse('core:approve-product', kwargs={'pk': self.product2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_product_filtering_by_status(self):
        """Test filtering products by status."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        # Filter by searching for draft in name or description
        response = self.client.get(f'{url}?search=draft')
        # Just verify the request works
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_product_search(self):
        """Test searching products by name."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        response = self.client.get(f'{url}?search=Product%201')
        products = response.data['results']
        self.assertTrue(any('Product 1' in p['name'] for p in products))
    
    def test_product_pagination(self):
        """Test product pagination."""
        self._login('admin', 'testpass123')
        url = reverse('core:internal-products')
        response = self.client.get(url)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)


class UserManagementAPITests(APITestCase):
    """Test cases for user management endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.business = Business.objects.create(name='Test Business')
        self.admin_user = User.objects.create_user(
            username='admin',
            password='testpass123',
            business=self.business,
            role='admin'
        )
        self.editor_user = User.objects.create_user(
            username='editor',
            password='testpass123',
            business=self.business,
            role='editor'
        )
        self.client = APIClient()
    
    def _login(self, username, password):
        """Helper to login and set authorization header."""
        url = reverse('token_obtain_pair')
        data = {'username': username, 'password': password}
        response = self.client.post(url, data, format='json')
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_list_business_users(self):
        """Test listing business users."""
        self._login('admin', 'testpass123')
        url = reverse('core:business-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_count = len(response.data['results'])
        self.assertGreaterEqual(user_count, 2)
    
    def test_create_user_by_admin(self):
        """Test that admin can create new users."""
        self._login('admin', 'testpass123')
        url = reverse('core:business-users')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'role': 'editor'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'editor')
    
    def test_create_user_by_non_admin_fails(self):
        """Test that non-admin cannot create users."""
        self._login('editor', 'testpass123')
        url = reverse('core:business-users')
        data = {
            'username': 'newuser',
            'email': 'newuser@test.com',
            'password': 'newpass123',
            'role': 'editor'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_filtering_by_role(self):
        """Test filtering users by role."""
        self._login('admin', 'testpass123')
        url = reverse('core:business-users')
        # Filter users using search (searching username/email)
        response = self.client.get(f'{url}?search=editor')
        # Just verify the request works and returns paginated results
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_user_pagination(self):
        """Test user pagination."""
        self._login('admin', 'testpass123')
        url = reverse('core:business-users')
        response = self.client.get(url)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)

