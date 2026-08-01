from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Verifies security settings before production deployment'
    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🔒 GestiFlow — Security Check\n'))
        checks = []
        checks.append(('❌ CRITIQUE' if settings.DEBUG else '✅', 'DEBUG=' + str(settings.DEBUG)))
        sk = settings.SECRET_KEY
        checks.append(('❌ CRITIQUE' if 'insecure' in sk.lower() or len(sk)<40 else '✅', f'SECRET_KEY ({len(sk)} chars)'))
        checks.append(('⚠️' if not settings.ALLOWED_HOSTS or '*' in settings.ALLOWED_HOSTS else '✅', f'ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}'))
        checks.append(('✅' if getattr(settings,'SESSION_COOKIE_HTTPONLY',True) else '❌ CRITIQUE', 'SESSION_COOKIE_HTTPONLY'))
        checks.append(('✅' if 'apps.core.security_middleware.SecurityHeadersMiddleware' in settings.MIDDLEWARE else '❌ CRITIQUE', 'SecurityHeadersMiddleware'))
        db_engine = settings.DATABASES.get('default',{}).get('ENGINE','')
        checks.append(('⚠️ ATTENTION' if 'sqlite' in db_engine else '✅', f'DB: {db_engine}'))
        critiques = warnings = 0
        for status, msg in checks:
            if '❌' in status:
                self.stdout.write(self.style.ERROR(f'  {status}  {msg}')); critiques+=1
            elif '⚠️' in status:
                self.stdout.write(self.style.WARNING(f'  {status}  {msg}')); warnings+=1
            else:
                self.stdout.write(self.style.SUCCESS(f'  {status}  {msg}'))
        self.stdout.write('')
        if critiques: self.stdout.write(self.style.ERROR(f'❌ {critiques} probleme(s) CRITIQUE(S)'))
        elif warnings: self.stdout.write(self.style.WARNING(f'⚠️  {warnings} avertissement(s)'))
        else: self.stdout.write(self.style.SUCCESS('✅ Tous les controles sont passes!'))
