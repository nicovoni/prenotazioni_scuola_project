# Copilot Instructions for prenotazioni_scuola_project

## Project Overview
This is a Django-based school reservation system, containerized with Docker. The backend is located in the `backend/` directory and follows standard Django project conventions, with customizations for deployment and developer workflow.

## Architecture & Key Components
- **backend/**: Django project root. Contains:
  - `manage.py`: Entry point for Django commands.
  - `config/`: Django settings, URLs, and WSGI config.
  - `prenotazioni/`: Main app for reservation logic (models, views, serializers, admin, URLs).
- **Dockerfile, docker-compose.yml, entrypoint.sh**: Used for containerized development and deployment. The web service runs Django inside a container.
- **requirements.txt**: Python dependencies for the backend.

## Developer Workflow
- **Environment Setup**: Copy `.env.example` to `.env` before starting. For production, set environment variables in Render using the same names (see below).
- **Build & Run (local)**: Use `docker-compose up -d --build` to build and start services.
- **Superuser Creation**: Run `docker-compose exec web python manage.py createsuperuser` to create an admin user.
- **Database Migrations**: Use `docker-compose exec web python manage.py migrate` for schema changes.
- **App Management**: All Django management commands should be run inside the container using `docker-compose exec web ...`.
- **Deploy on Render**: Configure a Render web service using the Dockerfile. Set environment variables (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DATABASE_URL`) in the Render dashboard. Use Supabase connection string as `DATABASE_URL`.

## Patterns & Conventions
- **App Structure**: Business logic is in `prenotazioni/`. Serializers are used for API data transformation.
- **Settings**: All configuration is in `config/settings.py`. Environment variables are loaded from `.env`.
- **URLs**: Main routing in `config/urls.py`, app-specific routes in `prenotazioni/urls.py`.
- **Admin**: Custom admin logic in `prenotazioni/admin.py`.
- **API**: Uses Django REST Framework (see `serializers.py`, `views.py`).

## Integration Points
- **External Dependencies**: All Python packages are listed in `requirements.txt`. Docker handles installation.
- **Environment Variables**: Managed via `.env` file for local, and via Render dashboard for production. Use Supabase credentials as placeholders in `.env.example`.
- **Database**: For production, use Supabase (PostgreSQL compatible). Set `DATABASE_URL` to the Supabase connection string: `postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:5432/<SUPABASE_DB>`.
- **Containerization**: All development and deployment is expected to be via Docker Compose locally, and via Dockerfile on Render.

## Examples
- To run tests: `docker-compose exec web python manage.py test prenotazioni`
- To apply migrations: `docker-compose exec web python manage.py migrate`
- To create a new app: `docker-compose exec web python manage.py startapp <appname>`

## Key Files
- `backend/config/settings.py`: Project settings
- `backend/prenotazioni/models.py`: Reservation models
- `backend/prenotazioni/views.py`: API views
- `backend/prenotazioni/serializers.py`: API serializers
- `Dockerfile`, `docker-compose.yml`: Container setup

---
Update this file if project structure or workflows change. For questions, check `README.md` or ask maintainers.
