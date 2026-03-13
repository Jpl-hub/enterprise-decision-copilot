from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.bootstrap_sample_data import ensure_sample_data


BASE_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "企航数策 Agent"
    target_industry: str = "医药生物"
    target_pool_mode: str = "core"
    target_pool_path: str = ""
    llm_base_url: str = "https://api.siliconflow.cn/v1"
    llm_api_key: str = ""
    llm_model: str = "Qwen/Qwen2.5-72B-Instruct"
    vision_llm_base_url: str = "https://api.siliconflow.cn/v1"
    vision_llm_api_key: str = ""
    vision_llm_model: str = "Qwen/Qwen2.5-VL-72B-Instruct"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    auth_token_ttl_hours: int = 72
    auth_cookie_name: str = "edc_session"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_cookie_domain: str = ""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def data_dir(self) -> Path:
        return BASE_DIR / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        return self.data_dir / "processed"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


settings = Settings()
ensure_sample_data(BASE_DIR)
