from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates a default superuser with username "admin" and password "admin123" if one does not already exist.'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        password = 'admin123'
        email = 'admin@example.com'  # you can change this if needed

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superuser "{username}" already exists.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}".'))
