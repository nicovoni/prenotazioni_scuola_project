"""
Comando per creare l'utente amministratore in sicurezza.

Uso:
    python manage.py create_admin_securely

Questa è l'UNICA forma sicura per creare l'admin iniziale.
Il comando:
1. Verifica che non esista un superuser
2. Verifica che il setup non sia già completato
3. Genera una password temporanea FORTE
4. Crea l'admin e la registra nel log
5. Mostra la password UNA SOLA VOLTA
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.utils import timezone
from prenotazioni.models import ConfigurazioneSistema
import secrets
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Create the initial admin user securely'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Admin email (es. admin@isufol.it)',
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Admin username (optional, derived from email if not provided)',
        )
        parser.add_argument(
            '--non-interactive',
            action='store_true',
            help='Non-interactive mode (requires --email)',
        )

    def handle(self, *args, **options):
        # =====================================================================
        # STEP 1: Verifica che non esista già un admin
        # =====================================================================
        existing_admins = User.objects.filter(is_superuser=True).count()
        if existing_admins > 0:
            raise CommandError(
                f'❌ Errore: {existing_admins} superuser esist(e) già.\n'
                f'Non è possibile creare un nuovo admin con questo comando.\n'
                f'Per modificare l\'admin, usa Django admin o psql/database editor.'
            )

        # =====================================================================
        # STEP 2: Verifica che il setup non sia completato
        # =====================================================================
        try:
            setup_completed = ConfigurazioneSistema.ottieni_configurazione(
                'SETUP_COMPLETED',
                default=None
            )
            if setup_completed:
                raise CommandError(
                    '❌ Errore: Setup già completato.\n'
                    'Usa Django admin per modificare l\'admin.\n'
                    'Per resettare il setup, contatta lo sviluppatore.'
                )
        except Exception as e:
            if 'Setup già completato' not in str(e):
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Attenzione: Non è possibile verificare SETUP_COMPLETED: {e}\n'
                        f'Continuerò comunque...'
                    )
                )

        # =====================================================================
        # STEP 3: Richiedi email admin
        # =====================================================================
        admin_email = options.get('email', '').strip()

        if not admin_email:
            if options.get('non_interactive'):
                raise CommandError(
                    '❌ Modalità non-interattiva: --email è obbligatorio'
                )
            admin_email = input(
                '📧 Email admin (es. admin@isufol.it): '
            ).strip()

        # Valida formato email
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, admin_email):
            raise CommandError(
                f'❌ Email non valida: {admin_email}'
            )

        # Verifica che l'email non sia già usata
        if User.objects.filter(email=admin_email).exists():
            raise CommandError(
                f'❌ Email già registrata: {admin_email}'
            )

        # =====================================================================
        # STEP 4: Determina username
        # =====================================================================
        admin_username = options.get('username', '').strip()

        if not admin_username:
            # Estrai da email (parte prima di @)
            admin_username = admin_email.split('@')[0].lower().replace('.', '_')

        # Verifica che l'username non sia già usato
        if User.objects.filter(username=admin_username).exists():
            raise CommandError(
                f'❌ Username già registrato: {admin_username}'
            )

        # =====================================================================
        # STEP 5: Genera password temporanea FORTE
        # =====================================================================
        # Usa secrets per una password crittograficamente sicura
        # base64 di 12 byte = ~16 caratteri, contiene maiuscole, minuscole, numeri
        temp_password = secrets.token_urlsafe(12)

        # =====================================================================
        # STEP 6: Crea l'admin nel database
        # =====================================================================
        try:
            admin_user = User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=temp_password
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superuser creato: {admin_username}')
            )
        except Exception as e:
            raise CommandError(
                f'❌ Errore durante la creazione dell\'admin: {e}'
            )

        # =====================================================================
        # STEP 7: Registra nel log di sistema
        # =====================================================================
        try:
            ConfigurazioneSistema.objects.create(
                chiave_configurazione='ADMIN_CREATION_LOG',
                valore_configurazione=(
                    f'Admin creato: {admin_email} ({admin_username}) '
                    f'at {timezone.now().isoformat()}'
                ),
                tipo_configurazione='sistema',
                descrizione_configurazione='Traccia della creazione dell\'admin tramite manage.py'
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Attenzione: Impossibile registrare nel log: {e}'
                )
            )

        # =====================================================================
        # STEP 8: Mostra OUTPUT IMPORTANTE (password ONE-TIME)
        # =====================================================================
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('✅ ADMIN CREATO CON SUCCESSO'))
        self.stdout.write('='*70)
        self.stdout.write(f'\n📧 Email: {admin_email}')
        self.stdout.write(f'👤 Username: {admin_username}')
        self.stdout.write(f'\n🔐 Password TEMPORANEA:\n   {temp_password}')
        self.stdout.write(
            self.style.WARNING(
                '\n⚠️  IMPORTANTE - LEGGI ATTENTAMENTE:\n'
                '   1. ✏️  COPIA questa password e salvala in LUOGO SICURO (password manager)\n'
                '   2. 🚫 NON condividerla mai, nemmeno con altri admin\n'
                '   3. 🔓 Al primo login su /accounts/login/admin/, dovrai cambiarla\n'
                '   4. 📝 La password non può essere recuperata dopo questo messaggio\n'
                '   5. 🔑 Se perdi la password, chiedi allo sviluppatore di resettarla\n'
            )
        )
        self.stdout.write('\n' + '='*70)
        self.stdout.write(
            self.style.SUCCESS(
                'Per iniziare:\n'
                f'  1. Accedi a: https://tuodominio.com/accounts/login/admin/\n'
                f'  2. Login: {admin_username} / {temp_password}\n'
                f'  3. Completa il wizard di configurazione\n'
            )
        )
        self.stdout.write('='*70 + '\n')
