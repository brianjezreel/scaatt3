from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates the default superuser account'

    def handle(self, *args, **options):
        try:
            username = 'brjezreel'
            email = 'brianjezreel.00@gmail.com'
            
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists'))
                return
                
            if User.objects.filter(email=email).exists():
                self.stdout.write(self.style.WARNING(f'User with email "{email}" already exists'))
                return
            
            # Create superuser
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='bjadmin',
                first_name='BJ',
                last_name='Bautista',
            )
            
            # Set role to teacher since superuser should be a teacher
            user.role = 'TEACHER'
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))
            
        except IntegrityError as e:
            self.stdout.write(self.style.ERROR(f'Error creating superuser: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Unexpected error: {e}')) 