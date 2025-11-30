# 📧 Modifiche alla Politica di Validazione Email

**Data**: 30 Novembre 2025  
**Obiettivo**: Rendere il sistema agnostico rispetto al dominio email e adattare gli accessi a qualsiasi istituto

---

## 🎯 Sommario delle Modifiche

### Primo Utente (Admin)
- ✅ Può usare **QUALSIASI dominio email** (non solo .edu.it)
- ✅ Può essere un'**email personale**
- ✅ Validazione: solo **formato email corretto** (via Django EmailField)
- ✅ **AVVISO CHIARO** nel form che diventerà admin e non potrà essere cambiato
- ✅ Una volta creato, il ruolo è **permanente e non modificabile**

### Altri Utenti (Docenti)
- ✅ Validazione **rimossa** da format/dominio hardcoded (`i.nizzo@isufol.it`)
- ✅ Accettano **qualsiasi formato email**
- ✅ In futuro: configurazione istituto-specifica tramite step di setup

---

## 📝 Dettagli delle Modifiche

### 1. **AdminUserForm** (`prenotazioni/forms.py`)

**Prima**:
```python
class AdminUserForm(forms.Form):
    """Minimal form used during initial setup to collect admin email."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'admin@example.edu.it'}),
        label='Email Amministratore'
    )
```

**Dopo**:
```python
class AdminUserForm(forms.Form):
    """Form per collezionare email primo utente che diventerà amministratore.
    
    IMPORTANTE:
    - Il primo utente che accede al sistema diventerà AUTOMATICAMENTE amministratore
    - Questo ruolo NON POTRÀ ESSERE CAMBIATO IN SEGUITO
    - L'email può essere un indirizzo personale (qualsiasi dominio)
    - La validazione è solo sul formato email (non sul dominio)
    
    Successivamente gli altri utenti (docenti con email scolastica) dovranno
    rispettare il formato e dominio configurati dall'istituto.
    """
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'admin@example.com'
        }),
        label='Email Amministratore',
        help_text='Può essere un indirizzo email personale (qualsiasi dominio)'
    )
    
    def clean_email(self):
        """Valida che l'email abbia un formato corretto.
        
        NOTE:
        - Qualsiasi dominio è accettato (non solo .edu.it)
        - La validazione del dominio per gli altri utenti sarà
          configurata in uno step successivo
        """
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise ValidationError('Questo campo non può essere vuoto.')
        
        # Semplice validazione: assicura che sia un'email valida
        # Django già valida il formato tramite EmailField
        # Qui non facciamo controlli sul dominio
        
        return email.lower()
```

**Cambiate**:
- ✅ Placeholder da `admin@example.edu.it` → `admin@example.com`
- ✅ Help text: aggiunto messaggio su "qualsiasi dominio"
- ✅ Validazione: rimosso controllo su dominio .edu.it
- ✅ Commenti: spiegato chiaramente il comportamento

---

### 2. **EmailLoginForm** (`prenotazioni/forms.py`)

**Prima**:
```python
class EmailLoginForm(forms.Form):
    """Form per login tramite email."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'i.cognome@isufol.it'
        }),
        label='Email Istituzionale'
    )
```

**Dopo**:
```python
class EmailLoginForm(forms.Form):
    """Form per login tramite email.
    
    La validazione del formato/dominio email verrà implementata
    durante lo step di configurazione del sistema per adattarsi
    alle specifiche esigenze dell'istituto.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'nome.cognome@dominio.it'
        }),
        label='Email Istituzionale',
        help_text='Inserisci la tua email scolastica'
    )
```

**Cambiate**:
- ✅ Placeholder da `i.cognome@isufol.it` → `nome.cognome@dominio.it` (generico)
- ✅ Help text generico: "Inserisci la tua email scolastica"
- ✅ Commenti: spiegato che validazione verrà configurata dopo

---

### 3. **Email Login Template** (`config/templates/registration/email_login.html`)

**Prima**:
```html
<input type="email" name="email" id="email" placeholder="i.cognome@isufol.it" ... required autofocus>
<div style="font-size: 13px; color: #6c757d; margin-top: 0.5rem; font-style: italic;">
    Formato: iniziale del nome + punto + cognome. Esempio: i.nizzo@isufol.it
</div>

<!-- JavaScript validation hardcoded per isufol.it -->
<script>
    function validateEmailForm(event) {
        var domain = 'isufol.it';
        var localRegex = /^[A-Za-z]\.[A-Za-zÀ-ÖØ-öø-ÿ']+[0-9]*$/i;
        // ... validation hardcoded ...
    }
</script>
```

**Dopo**:
```html
<input type="email" name="email" id="email" placeholder="nome.cognome@dominio.it" ... required autofocus>
<div style="font-size: 13px; color: #6c757d; margin-top: 0.5rem; font-style: italic;">
    Usa l'email scolastica fornita dal tuo istituto.
</div>
```

**Cambiate**:
- ✅ Placeholder generico: `nome.cognome@dominio.it`
- ✅ Help text generico: "Usa l'email scolastica fornita dal tuo istituto"
- ✅ **RIMOSSO completamente** lo script JavaScript con validazione hardcoded
- ✅ **RIMOSSO** l'alert su dominio isufol.it
- ✅ **RIMOSSO** il controllo su formato `i.nizzo`

---

### 4. **Wizard Setup Template** (`prenotazioni/templates/prenotazioni/configurazione_sistema.html`)

**Prima**:
```html
{% if step == "admin" or step == 1 %}
    <div class="card">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">👑 Passo 1: Crea Amministratore</h5>
        </div>
        <div class="card-body">
            {% if form_admin %}
            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label for="{{ form_admin.email.id_for_label }}" class="form-label">{{ form_admin.email.label }}</label>
                    {{ form_admin.email }}
                    ...
                    <div class="form-text">Inserisci l'email dell'amministratore del sistema.</div>
                </div>
                ...
            </form>
```

**Dopo**:
```html
{% if step == "admin" or step == 1 %}
    <div class="card">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">👑 Passo 1: Crea Amministratore</h5>
        </div>
        <div class="card-body">
            {% if form_admin %}
            <!-- ⚠️ AVVISO IMPORTANTE per primo utente admin -->
            <div class="alert alert-warning border-2" role="alert">
                <h5 class="alert-heading">
                    <i class="bi bi-exclamation-triangle"></i> Attenzione: Questa decisione è permanente!
                </h5>
                <hr>
                <p class="mb-2">
                    <strong>L'indirizzo email che inserirai diventerà l'amministratore del sistema.</strong>
                </p>
                <ul class="mb-3">
                    <li><strong>Non potrà mai essere cambiato in futuro</strong> - questo ruolo è permanente e esclusivo</li>
                    <li><strong>Può essere un'email personale</strong> - non deve necessariamente essere del dominio della scuola</li>
                    <li>Avrà accesso completo a tutte le funzionalità amministrative</li>
                    <li>Avrà accesso al wizard di configurazione e alle impostazioni di sistema</li>
                </ul>
                <p class="mb-0">
                    <strong>💡 Consiglio:</strong> Usa un'email che avrai accesso anche in futuro (es. email personale o email con permessi di accesso durevoli).
                </p>
            </div>

            <form method="post">
                {% csrf_token %}
                <div class="mb-3">
                    <label for="{{ form_admin.email.id_for_label }}" class="form-label">
                        <strong>{{ form_admin.email.label }}</strong>
                        <span class="text-danger">*</span>
                    </label>
                    {{ form_admin.email }}
                    {% if form_admin.email.help_text %}
                        <div class="form-text">{{ form_admin.email.help_text }}</div>
                    {% endif %}
                    ...
                </div>
                ...
            </form>
```

**Cambiate**:
- ✅ **AGGIUNTO** alert di avviso con sfondo giallo
- ✅ **AGGIUNTO** messaggio chiaro: "Questa decisione è permanente!"
- ✅ **AGGIUNTO** elenco bullet con requisiti chiari
- ✅ **AGGIUNTO** consiglio di usare email duratura
- ✅ **AGGIUNTO** help_text dal form nell'HTML

---

## 🔄 Flusso di Accesso Utenti

### 1. **Primo Accesso (Admin)**
```
Pagina /setup/admin/
  ↓
  Form: AdminUserForm
    - Email text input (qualsiasi dominio)
    - Avviso: "Diventerai admin, permanente, non modificabile"
    - Help: "Può essere email personale"
  ↓
  Validazione: Django EmailField (solo formato, no dominio)
  ↓
  Creazione: User con is_superuser=False (fatto da setup_amministratore)
```

### 2. **Accessi Successivi (Docenti)**
```
Pagina /login/ (email_login.html)
  ↓
  Form: EmailLoginForm
    - Email text input (placeholder generico)
    - Help: "Usa email scolastica fornita dal tuo istituto"
  ↓
  Validazione: Django EmailField (solo formato, no dominio per ora)
  ↓
  Login: Invia PIN se utente esiste
```

### 3. **In Futuro: Configurazione Dominio**
```
Wizard Step: "Configurazione Email Scolastica"
  ↓
  Admin specifica:
    - Dominio email (es: scuola.it)
    - Formato email (es: nome.cognome@scuola.it)
    - Pattern regex per validazione
  ↓
  Sistema memorizz: ConfigurazioneSistema
  ↓
  Validazione successiva: usar configurazione per verificare docenti
```

---

## ✅ Verifiche Effettuate

- ✅ Nessun hardcoded `i.nizzo@isufol.it` rimasto nel codice
- ✅ Nessun hardcoded `isufol.it` domain check nel codice
- ✅ AdminUserForm accetta qualsiasi email valida
- ✅ EmailLoginForm non controlla dominio
- ✅ Template email_login.html rimosso JS di validazione
- ✅ Wizard template mostra avviso chiaro per primo admin
- ✅ Placeholder placeholder generici in tutti i form

---

## 🚀 Prossimi Step (Futuri)

1. **Step di Configurazione Dominio**:
   - Aggiungere step nel wizard per dominio/formato email
   - Memorizzare in ConfigurazioneSistema
   - Usare per validazione accessi docenti

2. **Validazione Accessi Docenti**:
   - Leggere dominio da ConfigurazioneSistema
   - Validare email dei docenti contro dominio
   - Mostrare errore se non corrispondente

3. **Admin Panel**:
   - Permettere di modify dominio/formato DOPO setup
   - (ma NON admin email - quella rimane immutabile)

---

## 📌 Note Importanti

- **Admin email è immutabile**: Una volta scelto il primo admin, non può mai essere cambiato
- **Admin può usare email personale**: Questo è intenzionale - l'admin potrebbe anche non avere email scolastica
- **Validazione differita**: La validazione dominio-specifica verrà implementata dopo, non nel form base
- **Flessibilità**: Il sistema ora funziona con QUALSIASI istituto senza modifiche al codice

---

## 🧪 Testare le Modifiche

1. **Test primo admin**:
   - Accedi a `/setup/admin/` con DB vuoto
   - Inserisci email personale (es: `mario.rossi@gmail.com`)
   - Verifica che sia accettata
   - Leggi l'avviso di permanenza

2. **Test login docenti**:
   - Accedi a `/login/`
   - Prova email qualsiasi (es: `docente@scuola.it`)
   - Verifica che non verifichi dominio
   - Verifica che accetti formato

3. **Test validazione**:
   - Prova a inserire email invalida (es: `test@`)
   - Verifica che Django EmailField respinga
