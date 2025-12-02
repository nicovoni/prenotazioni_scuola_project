# Auto-generated migration: add ProfiloUtente password fields and PasswordHistory model
from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        # Add fields to ProfiloUtente
        migrations.AddField(
            model_name='profiloutente',
            name='must_change_password',
            field=models.BooleanField(default=False, help_text='Se True, l\u2019utente deve cambiare la password al successivo accesso', verbose_name='Forza cambio password'),
        ),
        migrations.AddField(
            model_name='profiloutente',
            name='password_last_changed',
            field=models.DateTimeField(blank=True, null=True),
        ),
        # Create PasswordHistory model
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password_hash', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='password_history', to='auth.user')),
            ],
            options={
                'verbose_name': 'Storico Password',
                'verbose_name_plural': 'Storico Password',
                'ordering': ['-created_at'],
            },
        ),
    ]
