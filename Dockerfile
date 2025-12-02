
FROM python:3.11-slim

# Variabili essenziali (esempio, da sovrascrivere in produzione)
ENV DJANGO_SECRET_KEY=changeme
ENV DATABASE_URL=sqlite:///db.sqlite3
ENV EMAIL_HOST_USER=your@email.com
ENV EMAIL_HOST_PASSWORD=yourpassword
ENV EMAIL_HOST=smtp-relay.brevo.com
ENV EMAIL_PORT=587
ENV EMAIL_USE_TLS=True
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN addgroup --system django && adduser --system --ingroup django django
RUN chown -R django:django /app
RUN chmod +x ./entrypoint.sh || true
USER django
EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--timeout", "90", "--capture-output", "--enable-stdio-inheritance", "--log-file", "-"]
