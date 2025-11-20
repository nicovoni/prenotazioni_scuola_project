# Dockerfile per Django app su Render
FROM python:3.11-slim

# Imposta working directory
WORKDIR /app

# Installa gcc per psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia tutto il progetto
COPY . .

# Crea utente non-root per sicurezza
RUN addgroup --system django && \
    adduser --system --ingroup django django

# Cambia proprietario dei file
RUN chown -R django:django /app

# Switcha all'utente non-root
USER django

# Espone la porta che Render fornisce via $PORT
EXPOSE 8000

# Comando di avvio
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
