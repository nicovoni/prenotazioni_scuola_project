# base image
FROM python:3.11-slim

# environment
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy backend
COPY backend/ /app/backend/

WORKDIR /app/backend

# start server
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:$PORT"]
