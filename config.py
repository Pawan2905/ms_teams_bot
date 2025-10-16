import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Azure OpenAI Settings
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
    azure_openai_embedding_deployment: str = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "")
    azure_openai_gpt_deployment: str = os.getenv("AZURE_OPENAI_GPT_DEPLOYMENT", "")
    
    # Jira and Confluence Settings
    atlassian_email: str = os.getenv("ATLASSIAN_EMAIL", "")
    atlassian_api_token: str = os.getenv("ATLASSIAN_API_TOKEN", "")
    jira_server: str = os.getenv("JIRA_SERVER", "")
    confluence_server: str = os.getenv("CONFLUENCE_SERVER", "")
    
    # For backward compatibility
    @property
    def jira_email(self) -> str:
        return self.atlassian_email
        
    @property
    def jira_api_token(self) -> str:
        return self.atlassian_api_token
        
    @property
    def confluence_email(self) -> str:
        return self.atlassian_email
        
    @property
    def confluence_api_token(self) -> str:
        return self.atlassian_api_token
    
    # Application Settings
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"

settings = Settings()
