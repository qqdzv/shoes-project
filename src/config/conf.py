from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

BASEDIR = Path(__file__).resolve().parent.parent.parent


class PostgresConfig(BaseModel):
    host: str
    port: int
    name: str
    user: str
    password: str

    @property
    def url(self) -> str:
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class Config(BaseSettings):
    debug: bool = False
    secret_key: str

    postgres: PostgresConfig

    model_config = SettingsConfigDict(
        extra="ignore",
        populate_by_name=True,
        case_sensitive=False,
        env_nested_delimiter="__",
        env_file=str(BASEDIR / ".env"),
    )


settings = Config()  # ty: ignore[missing-argument]
