import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Azure OpenAI LLM Settings
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_openai_gpt_deployment: str = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", "")
    
    # Azure OpenAI Embedding Settings
    azure_openai_embedding_api_key: str = os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY", "")
    azure_openai_embedding_endpoint: str = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT", "")
    azure_openai_embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
    
    # Jira Settings
    jira_server: str = os.getenv("JIRA_SERVER", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    
    # Confluence Settings
    confluence_server: str = os.getenv("CONFLUENCE_SERVER", "")
    confluence_email: str = os.getenv("CONFLUENCE_EMAIL", "")
    confluence_api_token: str = os.getenv("CONFLUENCE_API_TOKEN", "")
    
    # Application Settings
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    # Default data sources and schedule
    default_jira_project_key: str = os.getenv("DEFAULT_JIRA_PROJECT_KEY", "")
    default_confluence_space_key: str = os.getenv("DEFAULT_CONFLUENCE_SPACE_KEY", "")
    refresh_schedule_cron: str = os.getenv("REFRESH_SCHEDULE_CRON", "0 2 * * *")  # daily at 02:00
    refresh_days_back: int = int(os.getenv("REFRESH_DAYS_BACK", "7"))
    
    class Config:
        env_file = ".env"

settings = Settings()
