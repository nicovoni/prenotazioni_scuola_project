"""
Form Django per la validazione dei dati di prenotazione.
"""
from django import forms
from django.utils import timezone
from django.conf import settings
from .models import Prenotazione, Risorsa


class PrenotazioneForm(forms.Form):
    """
    Form per la creazione e modifica di prenotazioni.
    """
    risorsa = forms.ModelChoiceField(
        queryset=Risorsa.objects.all(),
        empty_label="Seleziona una risorsa",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'id_risorsa'})
    )

    data = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'min': timezone.now().date().isoformat()
        })
    )

    ora_inizio = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    ora_fine = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-control',
            'type': 'time'
        })
    )

    quantita = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'id': 'id_quantita'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.prenotazione_id = kwargs.pop('prenotazione_id', None)
        super().__init__(*args, **kwargs)

        # Aggiungi attributi data alle opzioni del select
        choices = [('', 'Seleziona una risorsa')]
        for risorsa in Risorsa.objects.all().order_by('tipo', 'nome'):
            choices.append((
                risorsa.id,
                risorsa.nome
            ))
        self.fields['risorsa'].choices = choices

        # Personalizza il widget per aggiungere data attributes
        self.fields['risorsa'].widget.attrs.update({
            'data-risorse': '|'.join([
                f"{r.id}:{r.tipo}:{r.quantita_totale}"
                for r in Risorsa.objects.all().order_by('tipo', 'nome')
            ])
        })

    def clean(self):
        """
        Validazione complessiva del form.
        """
        cleaned_data = super().clean()
        risorsa = cleaned_data.get('risorsa')
        data = cleaned_data.get('data')
        ora_inizio = cleaned_data.get('ora_inizio')
        ora_fine = cleaned_data.get('ora_fine')
        quantita = cleaned_data.get('quantita')

        if not (risorsa and data and ora_inizio and ora_fine and quantita):
            return cleaned_data

        # Validazione specifica per tipo di risorsa
        if risorsa.tipo == 'lab':
            # Laboratori: prenotazione dell'intero laboratorio (quantità = 1)
            if quantita != 1:
                raise forms.ValidationError("Per i laboratori è possibile prenotare solo l'intero spazio.")
        elif risorsa.tipo == 'carrello':
            # Carrelli: prenotazione parziale possibile
            if quantita > risorsa.quantita_totale:
                raise forms.ValidationError(f"Quantità richiesta ({quantita}) supera la disponibilità totale ({risorsa.quantita_totale}).")

        # Crea oggetti datetime per validazione
        try:
            inizio = timezone.datetime.combine(data, ora_inizio)
            fine = timezone.datetime.combine(data, ora_fine)
            inizio = timezone.make_aware(inizio)
            fine = timezone.make_aware(fine)
            now = timezone.now()

            # Validazioni temporali
            if inizio < now:
                raise forms.ValidationError("La data e ora di inizio devono essere nel futuro.")

            giorni_anticipo = settings.GIORNI_ANTICIPO_PRENOTAZIONE
            if (inizio.date() - now.date()).days < giorni_anticipo:
                raise forms.ValidationError(f"La prenotazione deve essere fatta almeno {giorni_anticipo} giorni prima.")

            # Controllo orari consentiti
            orario_inizio = ora_inizio.strftime('%H:%M')
            orario_fine = ora_fine.strftime('%H:%M')
            if orario_inizio < settings.BOOKING_START_HOUR or orario_fine > settings.BOOKING_END_HOUR:
                raise forms.ValidationError(f"Le prenotazioni sono consentite solo tra le {settings.BOOKING_START_HOUR} e le {settings.BOOKING_END_HOUR}.")

            # Controllo durata
            durata_min = settings.DURATA_MINIMA_PRENOTAZIONE_MINUTI
            durata_max = settings.DURATA_MASSIMA_PRENOTAZIONE_MINUTI
            durata = int((fine - inizio).total_seconds() // 60)

            if durata < durata_min:
                raise forms.ValidationError(f"La durata minima della prenotazione è di {durata_min} minuti.")
            if durata > durata_max:
                raise forms.ValidationError(f"La durata massima della prenotazione è di {durata_max} minuti.")
            if fine <= inizio:
                raise forms.ValidationError("L'orario di fine deve essere successivo a quello di inizio.")

            # Controllo disponibilità
            from .services import BookingService
            is_available, disponibile, errors = BookingService.check_resource_availability(
                risorsa.id, inizio, fine, quantita, exclude_booking_id=self.prenotazione_id
            )

            if not is_available:
                raise forms.ValidationError(errors[0])

            # Salva dati puliti per uso successivo
            cleaned_data['inizio'] = inizio
            cleaned_data['fine'] = fine

        except ValueError:
            raise forms.ValidationError("Data o orario non validi.")

        return cleaned_data


class ConfirmDeleteForm(forms.Form):
    """
    Form di conferma per eliminazione prenotazione.
    """
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
