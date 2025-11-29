# CSV-First Data Architecture

## Fonte Attendibile Unica

A partire da ora, il file **`backups/scuole_anagrafe.csv`** è l'unica fonte di verità per:
- Codici meccanografici delle scuole (CODICESCUOLA)
- Istituti principali e relative sedi affiliate (CODICEISTITUTORIFERIMENTO)
- Identificazione della sede di diritto (INDICAZIONESEDEDIRETTIVO = 'SI')
- Informazioni geografiche e di contatto delle sedi

## Architettura dei Dati

### 1. Lettura dal CSV (lookup_unica)

**File**: `prenotazioni/views.py::lookup_unica()`

La funzione:
- Legge direttamente dal CSV ad ogni richiesta (non usa cache JSON)
- Non salva l'indice come JSON persistente
- Costruisce un indice in memoria per la richiesta
- Restituisce l'istituto principale + plessi affiliati

```python
GET /api/lookup_unica/?codice=GRIS001009
→ Legge CSV
→ Trova GRIS001009 (sede_direttivo=SI) come principale
→ Trova affiliati: GRRI001509, GRPS00101Q, GRRI001011, GRTD00101G
→ Ritorna {data: {...}, affiliated_schools: [...]}
```

### 2. Popolazione di UbicazioneRisorsa

**Command**: `python manage.py populate_ubicazioni`

Legge dal CSV e popola la tabella `UbicazioneRisorsa`:
- Estrae tutti i plessi unici (CODICESCUOLA)
- Crea un record per ogni plesso con:
  - `nome` = DENOMINAZIONESCUOLA
  - `codice_meccanografico` = CODICESCUOLA
  - `edificio` = DESCRIZIONECOMUNE
  - `piano` = '1'
  - `aula` = nome abbreviato

Questo comando:
- Va eseguito una volta dopo aver messo a disposizione il CSV
- Può essere ri-eseguito per aggiornare i dati (aggiorna nome se cambiato)

```bash
python manage.py populate_ubicazioni --dry-run  # preview
python manage.py populate_ubicazioni             # esecuzione reale
```

### 3. Associazione Risorse a Plessi

**File**: `prenotazioni/views.py::setup_amministratore()` - step 'resources'

Quando l'utente crea una risorsa nel wizard e seleziona un plesso:
- Estrae il codice plesso dalla form (plesso_<n>)
- Cerca il record in `UbicazioneRisorsa` per `codice_meccanografico`
- Associa la risorsa al plesso tramite ForeignKey `localizzazione`

```python
plesso_codice = request.POST.get('plesso_1')  # es: "GRRI001509"
ubicazione = UbicazioneRisorsa.objects.filter(
    codice_meccanografico__iexact=plesso_codice
).first()
if ubicazione:
    risorsa.localizzazione = ubicazione
```

## Flusso Completo dell'Utente

1. **Step 1: Dati Amministratore** → Crea admin e scuola principale
2. **Step 2: Dati Scuola** 
   - Inserisce codice scuola (es: GRIS001009)
   - `lookup_unica()` legge dal CSV e ritorna:
     - Istituto principale: ISTITUTO ISTRUZIONE SUPERIORE FOLLONICA
     - Plessi affiliati: 4 sedi
3. **Step 3: Dispositivo** → Aggiunge dispositivo
4. **Step 4: Risorse**
   - Per ogni risorsa:
     - Nome risorsa (es: "Aula Informatica")
     - Tipo (es: "Aula")
     - **Plesso** (dropdown compilato da lookup_unica) ← NUOVO
     - Quantità
   - Al salvataggio: associa la risorsa al plesso tramite `UbicazioneRisorsa`
5. **Step 5: Completamento** → Wizard completato

## Vantaggi di questo Approccio

✅ **Single Source of Truth**: Un solo file CSV, senza sincronizzazione tra DB e file
✅ **Sempre Aggiornato**: Le modifiche al CSV sono immediatamente disponibili
✅ **Deterministico**: Stesso input (CSV) → Sempre stesso output
✅ **Audit Trail**: Storico delle modifiche nel file CSV
✅ **Facile da Gestire**: Un solo file da mantenere/backuppare

## Configurazione Richiesta

### File CSV
- **Path**: `backups/scuole_anagrafe.csv`
- **Encoding**: UTF-8
- **Colonne Necessarie**:
  - `CODICESCUOLA` (chiave primaria del plesso)
  - `DENOMINAZIONESCUOLA` (nome)
  - `CODICEISTITUTORIFERIMENTO` (istituto principale)
  - `INDICAZIONESEDEDIRETTIVO` (SI/NO per sede principale)
  - `DESCRIZIONECOMUNE`, `PROVINCIA`, `REGIONE` (dati geografici)
  - `INDIRIZZOSCUOLA` (indirizzo)

### Esecuzione Iniziale

```bash
# 1. Assicurati che il CSV sia in backups/scuole_anagrafe.csv
# 2. Popola UbicazioneRisorsa
python manage.py populate_ubicazioni

# 3. Verifica che i record siano stati creati
python manage.py shell
>>> from prenotazioni.models import UbicazioneRisorsa
>>> UbicazioneRisorsa.objects.count()  # Dovrebbe essere ~7860
>>> UbicazioneRisorsa.objects.filter(codice_meccanografico='GRIS001009').first()
```

## Manutenzione

- **Aggiornamento Dati**: Aggiorna il CSV e ri-esegui `populate_ubicazioni`
- **Verifica Coerenza**: Puoi validare che tutti i plessi nel CSV siano in DB:
  ```bash
  python manage.py populate_ubicazioni --verify
  ```
- **Backup**: Backup del CSV = backup dei dati delle scuole/plessi
