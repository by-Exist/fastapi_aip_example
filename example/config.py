from pydantic import BaseSettings as _BaseSettings


class _Settings(_BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite://"


settings = _Settings()  # type: ignore
