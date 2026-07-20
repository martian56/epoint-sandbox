from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_MERCHANTS = [
    ("i000000001", "sandbox_private_key_0000000001", "Sandbox Merchant"),
    ("i000000002", "sandbox_private_key_0000000002", "Split Partner"),
]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EPOINT_", env_file=".env", extra="ignore")

    port: int = 8181
    database_url: str = "postgresql+psycopg://epoint:epoint@localhost:5432/epoint_sandbox"
    public_base_url: str = "http://localhost:8181"

    callback_timeout_seconds: float = 10.0
    callback_max_attempts: int = 4
    callback_backoff_seconds: tuple[int, ...] = (60, 120, 180, 240)

    seed_merchants: bool = True
    web_dist_path: str = "static"

    # Both set turns on dashboard auth. Unset leaves it open, which is the local default.
    admin_email: str = ""
    admin_password: str = ""
    session_ttl_hours: int = 12

    # 3% per transaction, taken from epoint's payment history.
    commission_rate: float = 0.03


@lru_cache
def get_settings() -> Settings:
    return Settings()
