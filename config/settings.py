"""
Prime Spark AI - Configuration Management
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pathlib import Path


class EdgeInfrastructure(BaseSettings):
    """Edge infrastructure configuration"""
    router_ip: str = "192.168.1.1"
    nas_ip: str = "192.168.1.49"
    nas_port: int = 8080
    control_pc_ip: str = "192.168.1.100"
    spark_agent_ip: str = "192.168.1.92"

    model_config = SettingsConfigDict(env_prefix="EDGE_")


class CloudInfrastructure(BaseSettings):
    """Cloud infrastructure configuration"""
    primecore1_ip: str = "141.136.35.51"
    primecore1_port: int = 443
    primecore2_ip: str = ""
    primecore2_port: int = 443
    primecore3_ip: str = ""
    primecore3_port: int = 443
    primecore4_ip: str = "69.62.123.97"
    primecore4_port: int = 443

    model_config = SettingsConfigDict(env_prefix="PRIMECORE")


class VPNConfig(BaseSettings):
    """VPN configuration"""
    type: Literal["wireguard", "zerotier"] = "wireguard"
    port: int = 51820
    interface: str = "wg0"
    subnet: str = "10.8.0.0/24"
    control_pc_ip: str = "10.8.0.2"
    spark_agent_ip: str = "10.8.0.3"
    primecore1_ip: str = "10.8.0.11"
    primecore2_ip: str = "10.8.0.12"
    primecore3_ip: str = "10.8.0.13"
    primecore4_ip: str = "10.8.0.14"

    model_config = SettingsConfigDict(env_prefix="VPN_")


class MemoryConfig(BaseSettings):
    """Memory tier configuration"""
    # Tier 1: Local Cache (Redis)
    redis_local_port: int = 6379
    redis_password: str = "change_me_in_production"
    redis_max_memory: str = "2gb"
    redis_eviction_policy: str = "allkeys-lru"

    # Tier 2: NAS Persistent Storage
    nas_share_path: str = "/mnt/nas"
    nas_username: str = "primeai"
    nas_password: str = "change_me_in_production"

    # Tier 3: Cloud Storage
    supabase_url: str = ""
    supabase_key: str = ""
    minio_endpoint: str = "http://69.62.123.97:9000"
    minio_access_key: str = "change_me_in_production"
    minio_secret_key: str = "change_me_in_production"
    minio_bucket: str = "prime-spark-ai"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


class OllamaConfig(BaseSettings):
    """Ollama LLM configuration"""
    edge_url: str = "http://localhost:11434"
    cloud_url: str = "http://69.62.123.97:11434"
    default_model: str = "llama3.2:latest"

    model_config = SettingsConfigDict(env_prefix="OLLAMA_")


class APIConfig(BaseSettings):
    """API server configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    log_level: str = "info"

    model_config = SettingsConfigDict(env_prefix="API_")


class AuthConfig(BaseSettings):
    """Authentication configuration"""
    jwt_secret: str = "change_me_to_random_256bit_secret"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    admin_username: str = "admin"
    admin_password: str = "change_me_in_production"

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


class PowerConfig(BaseSettings):
    """Power management configuration"""
    mode: Literal["auto", "on-grid", "off-grid"] = "auto"
    battery_monitor_enabled: bool = True
    battery_low_threshold: int = 20
    battery_critical_threshold: int = 10

    model_config = SettingsConfigDict(env_prefix="POWER_")


class RoutingConfig(BaseSettings):
    """Request routing configuration"""
    strategy: Literal["edge-first", "cloud-first", "balanced"] = "edge-first"
    edge_timeout_seconds: int = 5
    cloud_fallback_enabled: bool = True
    max_retries: int = 3

    model_config = SettingsConfigDict(env_prefix="ROUTING_")


class MonitoringConfig(BaseSettings):
    """Monitoring configuration"""
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    grafana_enabled: bool = True
    grafana_port: int = 3000
    health_check_interval: int = 30

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


class HailoConfig(BaseSettings):
    """Hailo AI accelerator configuration"""
    enabled: bool = True
    device_id: int = 0

    model_config = SettingsConfigDict(env_prefix="HAILO_")


class LoggingConfig(BaseSettings):
    """Logging configuration"""
    level: str = "INFO"
    format: Literal["json", "text"] = "json"
    file: str = "/var/log/prime-spark-ai/app.log"

    model_config = SettingsConfigDict(env_prefix="LOG_")


class Settings(BaseSettings):
    """Main application settings"""
    edge: EdgeInfrastructure = EdgeInfrastructure()
    cloud: CloudInfrastructure = CloudInfrastructure()
    vpn: VPNConfig = VPNConfig()
    memory: MemoryConfig = MemoryConfig()
    ollama: OllamaConfig = OllamaConfig()
    api: APIConfig = APIConfig()
    auth: AuthConfig = AuthConfig()
    power: PowerConfig = PowerConfig()
    routing: RoutingConfig = RoutingConfig()
    monitoring: MonitoringConfig = MonitoringConfig()
    hailo: HailoConfig = HailoConfig()
    logging: LoggingConfig = LoggingConfig()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings instance
settings = Settings()
