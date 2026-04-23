# load_config.py
import yaml
import logging
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class AppConfig(BaseModel):
    name: str
    version: str
    description: str


class ServerConfig(BaseModel):
    host: str
    port: int


class OrchestratorAgentConfig(BaseModel):
    model: str   


class HotelSearchAgentConfig(BaseModel):
    model: str


class AgentConfig(BaseModel):
    orchestrator_agent: OrchestratorAgentConfig
    hotel_search_agent: HotelSearchAgentConfig 


class Config(BaseModel):
    app: AppConfig
    server: ServerConfig
    agents: AgentConfig


def load_config(path: str = "config.yaml") -> Config:
    config_path = Path(path)
    logger.info(f"Loading config from: {config_path.resolve()}",)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r") as f:
        raw = yaml.safe_load(f)
    config = Config(**raw)
    logger.info(f"Config loaded — app: {config.app.name}, version: {config.app.version}")
    return config

# Single importable CONFIG object
CONFIG = load_config()