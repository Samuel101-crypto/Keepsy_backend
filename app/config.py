from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str
    expiration_time: str
    mailjet_api_key: str
    mailjet_api_secret: str
    
    class Config:
        env_file = ".env"

settings = Settings()