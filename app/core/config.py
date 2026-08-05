from pydantic_settings import BaseSettings
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential


class Settings(BaseSettings):
    KEY_VAULT_URL: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DOCUMENT_DB_CONNECTION_STR: str = ""
    DOCUMENT_DATABASE_NAME: str = ""
    KAKAO_REST_API_KEY: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    IS_LOCAL: bool = True
    REDIRECT_URI: str = ""
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

# 배포 환경이면 Key Vault에서 모두 가져오기
if settings.KEY_VAULT_URL:
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=settings.KEY_VAULT_URL, credential=credential)

    for secret_property in client.list_properties_of_secrets():
        secret_name = secret_property.name.replace("-", "_")
        secret_value = client.get_secret(secret_property.name).value
        if hasattr(settings, secret_name):
            setattr(settings, secret_name, secret_value)