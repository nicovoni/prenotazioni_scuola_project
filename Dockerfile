# Optimized Python 3.11 slim base image for Render deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt /app/
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy the rest of the application
COPY . /app/

# Make sure scripts are executable
RUN chmod +x /app/manage.py /app/entrypoint.sh

# Expose port (Render sets PORT env var)
EXPOSE 10000

# Use entrypoint for migration and startup
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:10000", "--config", "gunicorn.conf.py"]
