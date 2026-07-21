from sqlalchemy.engine import URL
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    app_name: str = "Compass Survey Bot"
    app_version: str = "0.1.0"
    environment: str = "development"


    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = "postgres"
    postgres_port: int = 5432


    @property
    def database_url(self):

        return URL.create(
            drivername="postgresql+psycopg2",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


    class Config:
        env_file = ".env"


settings = Settings()
