# Event Planner

Multi-tenant SaaS for event planning, catering, souvenirs, and balloon/backdrop businesses.

Django REST API, Tailwind web UI, PostgreSQL, Redis/Celery, DigitalOcean Spaces.

## Stack

- Python 3.13 (Docker). Local tests also run on 3.12.
- Django 6.0.x (`django-celery-beat` does not support Django 6.1 yet)
- PostgreSQL 15, Redis 7
- JWT API at `/api/v1/`
- Session-auth web UI at `/login/`, `/dashboard/`, `/calendar/`

## Features

- Owner / admin / staff roles and store switching
- Email/password login (SSO later)
- Admin invites by email
- Clients, products, packages (pax pricing)
- Bookings, calendar, reschedule
- Contracts (HTML + WeasyPrint PDF)
- Team assignments
- Email and Twilio SMS reminders (UTC storage, user timezone display)

## Local setup

```bash
cp .env.example .env
docker compose up --build
```

Web UI: `http://localhost:8000`  
API: `http://localhost:8000/api/v1/`

Apply schema yourself (agent does not run DB commands):

```bash
docker compose exec web python manage.py migrate
```

Or apply Django contrib migrations, then `sql/0001_app_tables.postgresql.sql`.

Frontend assets:

```bash
npm install
npm run build
```

Tests:

```bash
pip install -r requirements/development.txt
DJANGO_SETTINGS_MODULE=config.settings.test pytest
```

## Auth

- Register with email, password, and IANA timezone
- JWT: `POST /api/v1/auth/login/` and `POST /api/v1/auth/refresh/`
- Web login: `/login/`
- Invite accept: `/invitations/<token>/`

## Production

```bash
docker compose -f docker-compose.prod.yml up --build
```

Apply schema yourself before serving traffic (compose does not run migrate):

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

Set these in your environment (do not commit secrets):

- `SECRET_KEY`, `ALLOWED_HOSTS`, `DJANGO_ENV=production`
- `DB_*`, `CELERY_*`
- `DO_SPACES_KEY`, `DO_SPACES_SECRET`, `DO_SPACES_BUCKET`, `DO_SPACES_ENDPOINT`
- `EMAIL_*` for SMTP
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` for SMS
- `FRONTEND_URL` (invite links; default `http://localhost:8000`)

WeasyPrint needs Pango (already in `Dockerfile`). SMS is skipped and marked failed when Twilio is unset.

## Calendar and timezones

Datetimes are stored in UTC. The UI uses the user's registration timezone. Calendar API accepts `?tz=` as an IANA override.

## API map

| Area | Prefix |
| --- | --- |
| Auth | `/api/v1/auth/` |
| Users / switch store | `/api/v1/users/` |
| Invitations | `/api/v1/invitations/` |
| Businesses | `/api/v1/businesses/` |
| Clients | `/api/v1/clients/` |
| Products / packages | `/api/v1/products/` |
| Bookings / calendar | `/api/v1/bookings/` |
| Contracts | `/api/v1/contracts/` |
| Team | `/api/v1/team/` |
| Reminders | `/api/v1/reminders/` |
