import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import User model
from django.contrib.auth import get_user_model
User = get_user_model()

def create_superuser():
    # Check if user already exists
    if User.objects.filter(username='brjezreel').exists():
        print('Superuser "brjezreel" already exists')
        return
        
    if User.objects.filter(email='brianjezreel.00@gmail.com').exists():
        print('User with email "brianjezreel.00@gmail.com" already exists')
        return
    
    try:
        # Create superuser
        user = User.objects.create_superuser(
            username='brjezreel',
            email='brianjezreel.00@gmail.com',
            password='bjadmin',
            first_name='BJ',
            last_name='Bautista',
        )
        
        # Set role to teacher
        user.role = 'TEACHER'
        user.save()
        
        print('Superuser "brjezreel" created successfully')
    except Exception as e:
        print(f'Error creating superuser: {e}')

if __name__ == '__main__':
    create_superuser() 