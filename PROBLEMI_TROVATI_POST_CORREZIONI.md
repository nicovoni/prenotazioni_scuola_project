# 🔴 PROBLEMI TROVATI DOPO CORREZIONI DATABASE

**Data**: 30 Novembre 2025  
**Severità**: CRITICA - Il wizard e alcune API sono rotte

---

## 📋 Riepilogo Problemi

| # | Gravità | Sistema | Problema | Impatto | Fix Priority |
|---|---------|---------|----------|--------|---|
| **1** | 🔴 CRITICA | Wizard Setup | DeviceWizardForm non ha campo `ubicazione` | Wizard fallisce step "device" | IMMEDIATO |
| **2** | 🔴 CRITICA | Wizard Setup | RisorseConfigurazioneForm non garantisce `localizzazione` | Wizard fallisce step "resources" | IMMEDIATO |
| **3** | 🟠 IMPORTANTE | API REST | BookingSerializer usa `dispositivi_selezionati` (rimosso) | API espone campo inesistente | ALTO |
| **4** | ✅ OK | Wizard Setup | Lookup codice_meccanografico | Funziona correttamente | - |
| **5** | ✅ OK | Views | `dispositivi_selezionati` non usato | No regressions | - |

---

## 🔴 PROBLEMA 1: DeviceWizardForm Manca Ubicazione

### Location
`prenotazioni/forms.py` linea 287-298

### Current Code
```python
class DeviceWizardForm(forms.ModelForm):
    """Form semplificato per wizard configurazione."""
    
    class Meta:
        model = Device
        fields = ['nome', 'tipo', 'marca', 'modello', 'categoria']
        # ❌ MANCA 'ubicazione'
        widgets = {
            'nome': forms.TextInput(...),
            'tipo': forms.Select(...),
            'marca': forms.TextInput(...),
            'modello': forms.TextInput(...),
            'categoria': forms.Select(...),
        }
```

### Model Requirement
`prenotazioni/models.py` linea 623-630:
```python
class Dispositivo(models.Model):
    # ...
    ubicazione = models.ForeignKey(
        UbicazioneRisorsa,
        on_delete=models.PROTECT,
        verbose_name='Ubicazione Dispositivo',
        # ❌ NOT NULL - obbligatoria!
    )
```

### Problem
- Wizard step 'device' cerca di creare Dispositivo (linea 175 views.py)
- Model richiede `ubicazione` NOT NULL
- Form non include il campo → **ValidationError al salvataggio**

### Where It Breaks
`prenotazioni/views.py` linea 175-180:
```python
if 'add_device' in request.POST:
    form_device = DeviceWizardForm(request.POST)
    context['form_device'] = form_device
    
    if form_device.is_valid():
        form_device.save()  # ❌ FALLISCE: ubicazione mancante
        messages.success(request, '✓ Dispositivo aggiunto!')
```

### Error Expected
```
django.db.utils.IntegrityError: NOT NULL constraint failed: prenotazioni_dispositivo.ubicazione_id
```

### Fix Required
1. Aggiungere `ubicazione` a DeviceWizardForm.Meta.fields
2. Aggiungere widget per selezione ubicazione (ChoiceField con QuerySet UbicazioneRisorsa)
3. Possibile aggiungere opzione "Crea nuova ubicazione" se nessuna esiste

---

## 🔴 PROBLEMA 2: RisorseConfigurazioneForm Non Garantisce Localizzazione

### Location
`prenotazioni/views.py` linea 245 (setup wizard step 'resources')

### Current Code
```python
risorsa = Risorsa(
    nome=nome,
    codice=codice,
    tipo=tipo_risorsa,
    capacita_massima=...,
    attivo=True
    # ❌ MANCA localizzazione!
)

# Tenta di assegnarla, ma se fallisce, salva senza
if plesso_codice:
    ubicazione = UbicazioneRisorsa.objects.filter(
        codice_meccanografico__iexact=plesso_codice
    ).first()
    if not ubicazione:
        ubicazione = UbicazioneRisorsa.objects.filter(
            nome__icontains=plesso_codice
        ).first()
    if ubicazione:
        risorsa.localizzazione = ubicazione
    # ❌ Se ubicazione non trovata, localizzazione rimane None!

risorsa.save()  # ❌ FALLISCE: localizzazione NOT NULL
```

### Model Requirement
`prenotazioni/models.py` linea 755-761:
```python
class Risorsa(models.Model):
    # ...
    localizzazione = models.ForeignKey(
        UbicazioneRisorsa,
        on_delete=models.PROTECT,
        # ❌ NOT NULL - obbligatoria!
    )
```

### Problem
- Risorsa richiede `localizzazione` NOT NULL
- Wizard prova a cercare ubicazione da `plesso_codice`
- Se non trova, salva Risorsa senza ubicazione → **IntegrityError**

### Where It Breaks
`prenotazioni/views.py` linea 245-253:
```python
if plesso_codice:
    ubicazione = ...  # Prova a trovare
    if ubicazione:
        risorsa.localizzazione = ubicazione
    # ❌ Se non trovata, localizzazione rimane None

risorsa.save()  # ❌ FALLISCE: localizzazione NOT NULL
```

### Error Expected
```
django.db.utils.IntegrityError: NOT NULL constraint failed: prenotazioni_risorsa.localizzazione_id
```

### Fix Required
1. Assicurare che SEMPRE esista una UbicazioneRisorsa valida prima di creare Risorsa
2. Opzioni:
   - a) Richiedere all'utente di selezionare ubicazione da dropdown
   - b) Se plesso_codice non match, creare automaticamente nuova UbicazioneRisorsa
   - c) Fallback a ubicazione "default" se esiste

---

## 🟠 PROBLEMA 3: BookingSerializer Usa Campo Rimosso

### Location
`prenotazioni/serializers.py` linea 176, 189, 206

### Current Code
```python
class BookingSerializer(serializers.ModelSerializer):
    # ...
    dispositivi_selezionati = DeviceSerializer(many=True, read_only=True)
    # ❌ Campo non esiste più in Prenotazione!
    
    class Meta:
        model = Prenotazione
        fields = [..., 'dispositivi_selezionati', ...]
        # ❌ Referenzia campo inesistente


class CreateBookingSerializer(serializers.ModelSerializer):
    # ...
    class Meta:
        model = Prenotazione
        fields = ['risorsa', 'dispositivi_selezionati', ...]  # ❌
```

### Model Reality
`prenotazioni/models.py` linea 990:
```python
# RIMOSSO: dispositivi_selezionati M2M
# SOSTITUITO DA: PrenotazioneDispositivo
# I dispositivi sono ora accedibili via: prenotazione.dispositivi_assegnati.all()
```

### Problem
- API REST endpoints usano questi serializers
- GET /api/bookings/ ritorna campo `dispositivi_selezionati` inesistente
- POST /api/bookings/ accetta campo `dispositivi_selezionati` che non fa nulla
- Nuovo modello `PrenotazioneDispositivo` non è esposto nell'API

### Where It Breaks
Qualsiasi client che:
- Aspetta `dispositivi_selezionati` in risposta GET
- Invia `dispositivi_selezionati` in POST (viene ignorato)
- Non può accedere al nuovo stato di assegnazione dispositivi

### Error Expected
```
AttributeError: 'Prenotazione' object has no attribute 'dispositivi_selezionati'
```
O semplicemente il campo appare null/assente

### Fix Required
1. Rimuovere `dispositivi_selezionati` dai serializers
2. Aggiungere nuovo serializer `PrenotazioneDispositivoSerializer` per tracciare device assignments
3. Aggiungere campo `dispositivi_assegnati` a BookingSerializer che usa PrenotazioneDispositivoSerializer
4. Opzionale: Aggiungere nested endpoint `/api/bookings/{id}/devices/`

---

## ✅ VERIFICHE PASSATE

### ✅ VERIFICA 1: Lookup Codice Meccanografico Funziona

**Location**: `prenotazioni/views.py` linea 262

**Code**:
```python
ubicazione = UbicazioneRisorsa.objects.filter(
    codice_meccanografico__iexact=plesso_codice
).first()
```

**Status**: ✅ OK - Campo esiste ancora in UbicazioneRisorsa

---

### ✅ VERIFICA 2: Views Non Usa M2M Dispositivi_Selezionati

**Search Result**: No matches in prenotazioni/views.py

**Status**: ✅ OK - Nessun uso di vecchio M2M

---

## 🔧 RACCOMANDAZIONE GENERALE

Le correzioni database erano corrette, ma **NON compatibili backwards con wizard e API**.

**Prossimi step necessari (in ordine)**:

1. **FIX CRITICA** (30 min):
   - Aggiornare DeviceWizardForm per richiedere ubicazione
   - Aggiornare RisorseConfigurazioneForm per garantire localizzazione
   - Testare wizard end-to-end

2. **FIX IMPORTANTE** (45 min):
   - Aggiornare BookingSerializer per usare PrenotazioneDispositivo
   - Creare PrenotazioneDispositivoSerializer
   - Testare API endpoints

3. **OPZIONALE** (se client web usato):
   - Aggiornare template prenota.html se fa POST dispositivi_selezionati
   - Aggiornare JavaScript per nuovo formato PrenotazioneDispositivo

---

## 📝 File da Aggiornare

### CRITICHE
- [ ] `prenotazioni/forms.py` - DeviceWizardForm (add ubicazione)
- [ ] `prenotazioni/forms.py` - RisorseConfigurazioneForm (garantire localizzazione)
- [ ] `prenotazioni/views.py` - step 'device' logic
- [ ] `prenotazioni/views.py` - step 'resources' logic

### IMPORTANTI
- [ ] `prenotazioni/serializers.py` - BookingSerializer
- [ ] `prenotazioni/serializers_corrected.py` - CreateBookingSerializer (se usato)
- [ ] `prenotazioni/views.py` - BookingViewSet (API)

### OPZIONALI
- [ ] `prenotazioni/templates/prenotazioni/prenota.html` - Se POST dispositivi

---

## 🎯 CONCLUSIONE

**Le correzioni database sono valide e corrette**, ma mancano update ai layer superiori (forms, views, serializers, templates).

Senza questi fix, il sistema non funzionerà:
- ❌ Wizard bloccato a step device/resources
- ❌ API espone campi inesistenti
- ⚠️ Client web potrebbero avere problemi

Stimato **1-2 ore** per completare tutti i fix.
