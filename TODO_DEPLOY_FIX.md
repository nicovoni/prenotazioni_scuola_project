# TODO: Fix Deploy Error - Python Path Issue

## Problema Identificato
❌ **Deploy Error**: `ModuleNotFoundError: No module named 'config'`
- Il PYTHONPATH nel render.yaml non puntava alla directory corretta
- Gunicorn non riesce a trovare il modulo `config` in `/app/backend/config/wsgi.py`

## Soluzione Applicata
✅ **CORREZIONE EFFETTUATA**
- [x] Correggere PYTHONPATH nel render.yaml da `/app` a `/app/backend`
- [x] Verificare modifica nel file render.yaml
- [x] Applicare correzione corretta

## Dettagli della Correzione
**Prima:**
```yaml
startCommand: cd backend && PYTHONPATH=/app gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
```

**Dopo:**
```yaml
startCommand: cd backend && PYTHONPATH=/app/backend gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120
```

## Test Richiesti
- [ ] Testare deploy con la correzione applicata
- [ ] Verificare che l'applicazione si avvii senza errori
- [ ] Aggiornare documentazione con la correzione
