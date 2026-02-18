"""
Management command to seed test data for the application.
Creates a test business and multiple users with different roles.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from core.models import Business, User, Product


class Command(BaseCommand):
    help = 'Seeds the database with test business and users'

    def handle(self, *args, **options):
        """Execute the seed data command."""
        
        # Create or get test business
        business, created = Business.objects.get_or_create(
            name='Test Business',
            defaults={'description': 'Test business for development'}
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created business: {business.name}')
            )
        else:
            self.stdout.write(f'Business already exists: {business.name}')
        
        # Define test users with roles
        test_users = [
            {
                'username': 'admin_user',
                'email': 'admin@test.com',
                'password': 'testpass123',
                'role': 'admin',
            },
            {
                'username': 'editor_user',
                'email': 'editor@test.com',
                'password': 'testpass123',
                'role': 'editor',
            },
            {
                'username': 'approver_user',
                'email': 'approver@test.com',
                'password': 'testpass123',
                'role': 'approver',
            },
            {
                'username': 'viewer_user',
                'email': 'viewer@test.com',
                'password': 'testpass123',
                'role': 'viewer',
            },
        ]
        
        # Create test users
        for user_data in test_users:
            password = user_data.pop('password')
            
            user, created = User.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'role': user_data['role'],
                    'business': business,
                    'is_active': True,
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created user: {user.username} ({user.get_role_display()})'
                    )
                )
            else:
                self.stdout.write(f'User already exists: {user.username}')
        
        # Create sample products
        sample_products = [
            {
                'name': 'Laptop',
                'description': 'High-performance laptop for professionals',
                'price': '999.99',
                'status': 'approved',
            },
            {
                'name': 'Smartphone',
                'description': 'Latest smartphone with advanced features',
                'price': '799.99',
                'status': 'approved',
            },
            {
                'name': 'Tablet',
                'description': 'Portable tablet for work and entertainment',
                'price': '499.99',
                'status': 'pending_approval',
            },
            {
                'name': 'Monitor',
                'description': '4K monitor for professional work',
                'price': '399.99',
                'status': 'draft',
            },
        ]
        
        admin_user = User.objects.filter(role='admin').first()
        
        for product_data in sample_products:
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'status': product_data['status'],
                    'business': business,
                    'created_by': admin_user,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created product: {product.name} ({product.get_status_display()})'
                    )
                )
            else:
                self.stdout.write(f'Product already exists: {product.name}')
        
        self.stdout.write(
            self.style.SUCCESS('\n✓ Test data seeding completed!')
        )
        self.stdout.write('\nTest Credentials:')
        self.stdout.write('  admin_user | testpass123 | Admin')
        self.stdout.write('  editor_user | testpass123 | Editor')
        self.stdout.write('  approver_user | testpass123 | Approver')
        self.stdout.write('  viewer_user | testpass123 | Viewer')
