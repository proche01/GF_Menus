# AGENTS.md

## Cursor Cloud specific instructions

### Architecture Overview

GF Finder is a Docker Compose-based application with 6 services: PostgreSQL+PostGIS (`db`), Redis, MinIO (S3-compatible storage), FastAPI backend, Celery worker, and Next.js frontend. See `README.md` for project structure and API endpoint reference.

### Running the Stack

All services run via Docker Compose:

```bash
docker compose up -d --build   # build and start all services
docker compose ps              # check service status
docker compose logs <service>  # view logs for a specific service
```

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs (Swagger):** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

### Docker in Cursor Cloud

Docker requires special setup in the Cloud Agent VM (nested containers). The Docker daemon must be started manually:

```bash
sudo dockerd &>/tmp/dockerd.log &
sleep 5
sudo chmod 666 /var/run/docker.sock
```

The fuse-overlayfs storage driver and iptables-legacy are required (configured in `/etc/docker/daemon.json`).

### Database Migrations

Alembic requires `psycopg2-binary` in the backend container (not in `requirements.txt`). Install before running migrations:

```bash
docker compose exec backend pip install psycopg2-binary
docker compose exec backend alembic upgrade head
```

The PostGIS image creates system tables (tiger geocoder) that Alembic autogenerate picks up. When generating new migrations, manually remove any PostGIS system table operations from the migration file.

### Key Gotchas

- **Enum values:** Models must use `values_callable` so SQLAlchemy persists lowercase enum values matching the DB (`"google"`, `"low"`, etc.). Alembic autogenerate still emits uppercase member names — manually fix generated migrations.
- **GeoAlchemy2 spatial index:** The `Geography` column type auto-creates a spatial index. Remove any duplicate `create_index` for `idx_restaurants_location` from generated migrations.
- **Geo casts:** Use `cast(..., Geography)` / `cast(..., Geometry)` from SQLAlchemy + GeoAlchemy2 types. Never use `func.cast(..., func.Geography)` (breaks SQLAlchemy cache keys).
- **Celery imports:** Tasks are registered via `celery_app.conf.imports` in `app/workers/celery_app.py`. Do not rely on `autodiscover_tasks` with nested task modules.
- **MinIO image:** Official `minio/minio` was removed from Docker Hub. Compose uses `pgsty/minio:latest`.
- **Sync DB URL:** Use `postgresql+psycopg2://...` for `DATABASE_URL_SYNC` (SQLAlchemy 2.1+ resolves bare `postgresql://` to psycopg3).
- **Free-tier caps:** Defaults cap discovery to 2 restaurants and 1 photo/source, use `gpt-4o-mini` + Vision `detail=low`, and skip Yelp photo downloads. Override via env if needed.
- **Frontend ESLint:** No `eslint.config.mjs` exists yet. `next lint` is deprecated in Next.js 15+ and requires interactive config, so it cannot be run non-interactively.
- **Frontend TypeScript:** There are pre-existing type errors in `restaurant/[slug]/page.tsx` and `restaurant/[slug]/menu/page.tsx` (`MenuItem[]` vs `GFMenuItem[]`). `next build` fails, but `next dev` works fine.
- **Backend tests:** Only `conftest.py` exists in `backend/tests/` with a fixture. No test files exist yet (`pytest` exits with code 5 = no tests collected).
- **External APIs:** The backend starts without API keys, but restaurant discovery/OCR/classification require valid `GOOGLE_PLACES_API_KEY`, `YELP_API_KEY`, and `OPENAI_API_KEY` in `backend/.env`.

### Commands Reference

| Task | Command |
|------|---------|
| Install backend deps (local) | `pip install -r backend/requirements.txt` |
| Install frontend deps (local) | `cd frontend && npm install` |
| Run backend tests | `cd backend && python3 -m pytest tests/ -v` |
| TypeScript check | `cd frontend && npx tsc --noEmit` |
| Frontend dev server | Runs inside Docker via `npm run dev` on port 3000 |
| Backend dev server | Runs inside Docker via `uvicorn` with `--reload` on port 8000 |
