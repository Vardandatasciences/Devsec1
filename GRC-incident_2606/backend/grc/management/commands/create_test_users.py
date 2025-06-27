from django.core.management.base import BaseCommand
from grc.models import User
from django.utils import timezone

class Command(BaseCommand):
    help = 'Creates test users in the database'

    def handle(self, *args, **kwargs):
        # Create system user (UserId=1) if it doesn't exist
        system_user, created = User.objects.get_or_create(
            UserId=1,
            defaults={
                'UserName': 'System',
                'Password': 'system123',
                'email': 'system@example.com',
                'CreatedAt': timezone.now(),
                'UpdatedAt': timezone.now()
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created system user'))
        else:
            self.stdout.write(self.style.SUCCESS('System user already exists'))

        # Create test users
        test_users = [
            {
                'UserName': 'Test User 1',
                'Password': 'test123',
                'email': 'test1@example.com'
            },
            {
                'UserName': 'Test User 2',
                'Password': 'test123',
                'email': 'test2@example.com'
            },
            {
                'UserName': 'Admin User',
                'Password': 'admin123',
                'email': 'admin@example.com'
            }
        ]

        for user_data in test_users:
            user, created = User.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'UserName': user_data['UserName'],
                    'Password': user_data['Password'],
                    'CreatedAt': timezone.now(),
                    'UpdatedAt': timezone.now()
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {user.UserName}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'User already exists: {user.UserName}')
                ) 