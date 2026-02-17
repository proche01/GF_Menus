# GF Finder -- Gluten-Free Menu Finder

AI-powered restaurant menu analysis for celiac and gluten-sensitive diners. Scrapes menu photos from Google Places and Yelp, uses OpenAI Vision for OCR and gluten-free classification, and generates searchable GF menus with safety ratings.

## Architecture

- **Frontend:** Next.js 15 (App Router, React 19, TailwindCSS, Leaflet maps)
- **Backend:** FastAPI (async, Pydantic v2, SQLAlchemy 2.0)
- **Database:** PostgreSQL 16 + PostGIS (geospatial queries)
- **Queue:** Celery + Redis (background menu ingestion pipeline)
- **Storage:** MinIO (S3-compatible, for menu photos)
- **AI:** OpenAI GPT-4o Vision (menu OCR + GF classification)

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys for: Google Places, Yelp Fusion, OpenAI

### Setup

1. Clone the repository and configure environment:

```bash
cd gluten-free-finder
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
```

2. Start all services:

```bash
docker compose up --build
```

3. Access the application:
   - **Frontend:** http://localhost:3000
   - **Backend API:** http://localhost:8000
   - **API Docs:** http://localhost:8000/docs
   - **MinIO Console:** http://localhost:9001 (minioadmin/minioadmin)

### Run Database Migrations

```bash
docker compose exec backend alembic upgrade head
```

### Trigger Restaurant Discovery

```bash
curl -X POST "http://localhost:8000/api/restaurants/discover?latitude=40.7128&longitude=-74.0060&radius_m=5000"
```

## Project Structure

```
gluten-free-finder/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Pydantic Settings
│   │   ├── database.py          # Async SQLAlchemy
│   │   ├── models/              # ORM models (Restaurant, Menu*, etc.)
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   │   └── gf_analysis/     # GF classifier, profiles, menu generator
│   │   ├── integrations/        # Google, Yelp, OpenAI clients
│   │   └── workers/tasks/       # Celery ingestion pipeline
│   ├── alembic/                 # Database migrations
│   └── tests/
└── frontend/
    └── src/
        ├── app/                 # Next.js pages
        ├── components/          # React components
        ├── lib/                 # API client, types
        └── hooks/               # React Query hooks, Zustand stores
```

## Key API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/search/restaurants` | Search with geo, filters, sorting |
| GET | `/api/restaurants/{id}` | Restaurant detail |
| GET | `/api/restaurants/map` | Map pins within bounds |
| POST | `/api/restaurants/discover` | Trigger background discovery |
| GET | `/api/menus/{id}/photos` | Menu photos with presigned URLs |
| GET | `/api/menus/{id}/items` | Menu items (optional `?gf_only=true`) |
| GET | `/api/menus/{id}/gf-menu` | Generated GF menu by sensitivity profile |
| GET | `/api/menus/{id}/safe-count` | Quick safe item count |

## Ingestion Pipeline

```
Discover Restaurants (Google/Yelp)
  -> Scrape Menu Photos
    -> Store in S3
      -> OCR via OpenAI Vision
        -> GF Classification
          -> Generate GF Menus
            -> Update DB counts
```

Each step is a Celery task that automatically chains to the next.
