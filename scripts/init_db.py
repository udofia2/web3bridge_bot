from app.config import load_settings
from app.db.base import create_all, init_engine


def main() -> None:
    settings = load_settings()
    init_engine(settings.database_url)
    create_all()
    print("Database initialized")


if __name__ == "__main__":
    main()
