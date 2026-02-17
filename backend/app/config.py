from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "GF Menu Finder API"
    debug: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://gfuser:gfpass@localhost:5432/gffinder"
    database_url_sync: str = "postgresql://gfuser:gfpass@localhost:5432/gffinder"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # S3 / MinIO
    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket_raw_photos: str = "menu-photos-raw"
    s3_bucket_processed_photos: str = "menu-photos-processed"
    s3_bucket_user_uploads: str = "user-uploads"

    # Google Places API
    google_places_api_key: str = ""

    # Yelp Fusion API
    yelp_api_key: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # JWT (v1+)
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
