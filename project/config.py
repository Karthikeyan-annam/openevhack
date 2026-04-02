"""Configuration module for Smart Waste Management Environment."""

import os
from typing import Optional


class Config:
    """Application configuration."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
    API_BASE_URL: str = os.getenv("API_BASE_URL", "https://api.openai.com/v1")

    # Hugging Face
    HF_TOKEN: str = os.getenv("HF_TOKEN", "")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Environment
    DEFAULT_TASK: str = os.getenv("DEFAULT_TASK", "medium")

    # Inference
    NUM_EPISODES_PER_TASK: int = int(os.getenv("NUM_EPISODES_PER_TASK", "3"))
    MAX_STEPS_PER_EPISODE: Optional[int] = None

    @staticmethod
    def validate():
        """Validate configuration."""
        if not Config.OPENAI_API_KEY:
            print("⚠ OPENAI_API_KEY not set. LLM features will be disabled.")
        
        return True

    @staticmethod
    def to_dict():
        """Return configuration as dictionary."""
        return {
            "openai_api_key": "***" if Config.OPENAI_API_KEY else "Not set",
            "model_name": Config.MODEL_NAME,
            "api_base_url": Config.API_BASE_URL,
            "host": Config.HOST,
            "port": Config.PORT,
            "debug": Config.DEBUG,
            "default_task": Config.DEFAULT_TASK,
            "num_episodes_per_task": Config.NUM_EPISODES_PER_TASK,
        }


if __name__ == "__main__":
    Config.validate()
    import json
    print(json.dumps(Config.to_dict(), indent=2))
