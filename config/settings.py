import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    """Configuración centralizada cargada desde el archivo .env."""

    DB_HOST: str = os.getenv("DB_HOST", "localhost").strip()
    DB_PORT: int = int(os.getenv("DB_PORT", "3306").strip())
    DB_USER: str = os.getenv("DB_USER", "root").strip()
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "database").strip()
    PEPPER_SECRET: str = os.getenv(
        "PEPPER_SECRET",
        "default_dev_pepper_secret_cambiar_en_produccion_inmediatamente_2026",
    ).strip()

    @classmethod
    def get_db_config(cls) -> dict:
        if not cls.DB_HOST or not cls.DB_USER or not cls.DB_NAME:
            raise ValueError(
                "Configuración de base de datos incompleta. Revisa tu archivo .env."
            )
        return {
            "host": cls.DB_HOST,
            "port": cls.DB_PORT,
            "user": cls.DB_USER,
            "password": cls.DB_PASSWORD,
            "database": cls.DB_NAME,
            "use_pure": True,
            "autocommit": False,
        }

    @classmethod
    def get_pepper_bytes(cls) -> bytes:
        if len(cls.PEPPER_SECRET) < 16:
            raise ValueError(
                "PEPPER_SECRET en .env es demasiado corto. Debe tener al menos 16 caracteres."
            )
        return cls.PEPPER_SECRET.encode("utf-8")
