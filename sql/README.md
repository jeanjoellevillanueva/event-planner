# Database SQL

Do not apply these from the agent environment. Run them yourself against PostgreSQL.

1. Apply Django built-in tables first (`auth`, `admin`, `sessions`, `contenttypes`, JWT blacklist, celery-beat).
2. Apply `0001_app_tables.postgresql.sql` for Event Planner tables.

Prefer Django migrations in Docker if you are not applying SQL by hand:

```bash
docker compose exec web python manage.py migrate
```

Host access to this project's Postgres (does not use 5432):

```bash
psql -h localhost -p 6543 -U event_planner -d event_planner
```
