# Usa un'immagine Python leggera
FROM python:3.11-slim

# Imposta variabile di ambiente
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Crea cartella app
WORKDIR /app

# Installa dipendenze
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copia il backend
COPY backend/ /app/backend/

# Copia entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Imposta directory di lavoro
WORKDIR /app/backend

# Comando di avvio
CMD ["/app/entrypoint.sh"]
