from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    expiration_time: str
    mailjet_api_key: str
    mailjet_api_secret: str
    publisher_url:str
    api_key: str
    vault_id: str
    tusky_files_url: str
    
    class Config:
        env_file = ".env"

settings = Settings()