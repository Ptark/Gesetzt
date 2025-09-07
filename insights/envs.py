from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Env(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir=".secrets")

    google_api_key: SecretStr | None = None
