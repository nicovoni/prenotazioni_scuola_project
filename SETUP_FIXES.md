# Problemi di setup: elenco, riproduzione e azioni consigliate

Questo documento raccoglie i problemi riscontrati durante il wizard di setup, i passaggi per riprodurli e le azioni consigliate (priorità e verifiche). Usa questo file come checklist operativa.

## Sommario veloce
- Mappa Leaflet non si visualizza correttamente nella pagina di configurazione della scuola.
- Dopo lookup CSV il form segnala: `indirizzo_scuola: Seleziona un suggerimento valido dall'elenco (scegli la scuola)` anche se i campi visibili sono popolati.
- Nel passo `device` il dispositivo appena aggiunto non appare nel catalogo subito dopo il salvataggio.
- Se il wizard viene riavviato può ricreare un amministratore: il wizard deve riprendere dallo step interrotto e non creare duplicati.

---

## 1) Map rendering (Passo `school`)
- Problema: l'elemento `#map_preview` rimane vuoto o non visibile dopo il lookup/autocomplete; il marker non appare.

### Riproduzione
1. Aprire: `/api/setup/?step=school`
2. Eseguire lookup (inserire codice meccanografico valido) o selezionare un suggerimento dall'autocomplete.
3. Osservare che il campo `indirizzo` è popolato ma la mappa non viene mostrata o è vuota.

### Azioni consigliate
- Assicurarsi che `#map_preview` sia presente nel DOM *prima* dell'inizializzazione della mappa.
- Chiamare `map.invalidateSize()` dopo che il container diventa visibile (timeout breve, es. 200ms) per forzare il rendering.
- Gestire gli errori JS che possano interrompere l'esecuzione (Console → correggere eventuali eccezioni).
- Acceptance: la mappa appare in fondo al form e il marker è visibile e centrato.

---

## 2) Lookup CSV e validazione indirizzo
- Problema: quando l'autofill viene da CSV (non da Nominatim), la validazione server-side richiede `osm_id`/`osm_type` e fallisce.

### Riproduzione
1. Inserire codice meccanografico valido e lasciare che il lookup CSV compili il form.
2. Cliccare "Salva e Continua".
3. Osservare l'errore `Seleziona un suggerimento valido dall'elenco (scegli la scuola)` per `indirizzo_scuola`.

### Azioni consigliate
- Lato client: impostare i campi hidden `id_osm_id_scuola` e `id_osm_type_scuola` quando il payload proviene dal CSV (es. `osm_type='csv'`, `osm_id='csv_<codice>'`).
- Lato server: aggiornare `InformazioniScuolaForm.clean_indirizzo_scuola` per accettare `osm_type='csv'` e usare i campi lat/lon e i componenti dell'indirizzo già forniti dal client senza chiamare Nominatim.
- Acceptance: invio del form dopo lookup CSV non produce l'errore e i campi hidden risultano nel POST.

---

## 3) Dispositivo non visibile dopo creazione (Passo `device`)
- Problema: aggiungi un dispositivo nel wizard, la pagina si ricarica ma il dispositivo non compare nella lista del catalogo.

### Riproduzione
1. Vai a `/api/setup/?step=device`.
2. Aggiungi un dispositivo usando il form del wizard e conferma.
3. Dopo reload, controlla la lista dei dispositivi o il catalogo: il nuovo dispositivo non è presente.

### Azioni consigliate
- Riprodurre localmente con logging della view che processa il POST del dispositivo.
- Verificare che l'istanza `Dispositivo` venga salvata (chiamata a `save()` o transaction commit) e che la query che costruisce il contesto della pagina includa i dispositivi appena creati.
- Controllare possibili filtri (es. `attivo=True`) oppure scope temporale/owner che esclude il dispositivo appena creato.
- Aggiungere test di integrazione che creino un dispositivo tramite la view-wizard e controllino la presenza nella successiva renderizzazione.

---

## 4) Wizard: riprendere da dove si era interrotto (evitare duplicazione admin)
- Problema: se il wizard si interrompe può ricreare il primo admin; serve persistere lo stato e impedire duplicazioni.

### Riproduzione
1. Avvia il wizard e crea il primo admin ma interrompi prima di completare gli step.
2. Riavvia il wizard: osserva che viene offerta nuovamente la creazione di un admin.

### Azioni consigliate
- Persistere lo stato corrente del wizard (sessione + DB): salvare `current_step` o `session['setup_step']` e l'`admin_user_id` creato già in sessione/DB.
- Verificare `ConfigurazioneSistema` per la chiave `SETUP_COMPLETED`; impedire la creazione di un admin se un admin esiste già o se `SETUP_COMPLETED` è impostato.
- Rendere la creazione admin atomica: creare l'utente e segnare lo stato parziale in sessione/DB in un unico flusso controllato.
- Acceptance: riavviando il wizard non si crea un secondo admin e l'utente riprende dallo step in cui si era interrotto.

---

## 5) Miglioramento popup marker
- Richiesta: mostrare nome scuola in grassetto + indirizzo su riga separata.

### Azione consigliata
- Aggiornare `showMap()` per compilare HTML per il popup: `<strong>Nome scuola</strong><br/><small>Via ...</small>` e legarlo al marker con `bindPopup()`.
- Acceptance: popup mostra nome e indirizzo; non blocca il form.

---

## 6) Test automatici e checklist manuale
- Aggiungere test unitari e di integrazione per i punti sopra:
  - `InformazioniScuolaForm.clean_indirizzo_scuola` con `osm_type='csv'`.
  - Flow di lookup CSV → popolamento form → POST riuscito.
  - Creazione dispositivo nel wizard e sua immediata presenza nella lista.

### Checklist manuale (per QA)
- [ ] Map: lookup → mappa visibile → marker popup con nome
- [ ] CSV lookup: lookup → form popolato → POST senza errori `indirizzo_scuola`
- [ ] Device: aggiungi dispositivo → appare nella lista
- [ ] Wizard resume: interrompi e riapri → non ricrea admin, riprende dallo step giusto

---

## Comandi utili per test (PowerShell)
- Avviare server di sviluppo:

```powershell
python manage.py runserver
```

- Richiedere il JSON di lookup (es. `GRIS001009`):

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/lookup_unica/?codice=GRIS001009" -UseBasicParsing
```

- Eseguire POST del form di setup da terminale (semplice esempio, adattare i campi):

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/setup/?step=school" -Method POST -Body @{ 'nome_completo_scuola'='Test'; 'indirizzo_scuola'='Via Roma 1'; 'osm_id_scuola'='csv_GRIS001009'; 'osm_type_scuola'='csv' }
```

---

## Priorità suggerita
1. Fix map rendering (bloccante UX)
2. Fix CSV lookup hidden fields + form acceptance (bloccante submit)
3. Investigare device creation bug
4. Wizard resume / prevenzione duplicati admin
5. Popup UX e test/QA

---

Se vuoi, posso generare le patch per i punti 1–3 in ordine e aggiungere i test di integrazione (posso iniziare ora con il punto 1).