from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    da24_api_url: str = "http://localhost:8001"
    admin_secret: str = "change-me"
    mssql_server: str = ""
    mssql_database: str = ""
    mssql_username: str = ""
    mssql_password: str = ""
    mcp_port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
