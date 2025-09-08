from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


SECRETS_DIR = ".secrets"


class Env(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir=SECRETS_DIR)

    google_api_key: SecretStr | None = None
