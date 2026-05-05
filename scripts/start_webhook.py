import uvicorn

from app.config import load_settings


def main() -> None:
    settings = load_settings()
    uvicorn.run("app.api.server:api", host=settings.host, port=settings.port, reload=False)


if __name__ == "__main__":
    main()
