from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Creates demo users and sample data'
    def handle(self, *args, **options):
        User = get_user_model()
        users = [
            ('admin',      'admin123',    'admin',      'Admin',      'GestiFlow'),
            ('manager',    'manager123',  'manager',    'Manager',    'GestiFlow'),
            ('vendeur',    'vendeur123',  'vendeur',    'Vendeur',    'GestiFlow'),
            ('technicien', 'tech123',     'technicien', 'Technicien', 'GestiFlow'),
            ('comptable',  'compta123',   'comptable',  'Comptable',  'GestiFlow'),
        ]
        for username, pwd, role, first, last in users:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(
                    username=username, password=pwd,
                    first_name=first, last_name=last,
                    email=f'{username}@gestiflow.dz',
                )
                u.role  = role
                u.actif = True
                if role == 'admin': u.is_staff = True; u.is_superuser = True
                u.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ User created: {username} / {pwd}'))
            else:
                self.stdout.write(f'  ⏭  User exists: {username}')
        self.stdout.write(self.style.SUCCESS('\n✅ Demo setup complete!'))
        self.stdout.write('\nLogin credentials:')
        for username, pwd, role, _, _ in users:
            self.stdout.write(f'  {role:12s} → {username} / {pwd}')
