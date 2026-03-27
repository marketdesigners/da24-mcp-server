from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    da24_api_url: str = "http://localhost:8001"
    admin_secret: str  # 기본값 없음 — 환경변수 미설정 시 시작 실패
    mssql_server: str = ""
    mssql_database: str = ""
    mssql_username: str = ""
    mssql_password: str = ""
    mcp_port: int = 8000

settings = Settings()
