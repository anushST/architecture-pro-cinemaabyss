from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PORT: int
    MONOLITH_URL: str
    MOVIES_SERVICE_URL: str
    GRADUAL_MIGRATION: bool
    MOVIES_MIGRATION_PERCENT: int

    model_config = SettingsConfigDict(extra="ignore")


settings = Settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    'formatters': {
        "default": {
            "format": "%(asctime)s|%(name)s|%(levelname)s|%(message)s|"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.access": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
}
