import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    groq_api_key: str
    groq_model: str
    groq_temperature: float
    user_agent: str
    http_timeout_seconds: int
    http_retry_count: int
    http_retry_backoff_seconds: float
    web_search_provider: str
    cors_origins: str
    alpha_vantage_api_key: str
    cache_ttl_seconds: int
    rate_limit_min_interval: float
    sec_user_agent: str
    citadel_refresh_interval_seconds: int
    openfigi_api_key: str
    gdelt_max_records: int


def load_settings() -> Settings:
    return Settings(
        groq_api_key=os.getenv("GROQ_API_KEY", ""),
        groq_model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        groq_temperature=float(os.getenv("GROQ_TEMPERATURE", "0.2")),
        user_agent=os.getenv("USER_AGENT", "FinancialLLM/1.0"),
        http_timeout_seconds=int(os.getenv("HTTP_TIMEOUT_SECONDS", "30")),
        http_retry_count=int(os.getenv("HTTP_RETRY_COUNT", "3")),
        http_retry_backoff_seconds=float(os.getenv("HTTP_RETRY_BACKOFF_SECONDS", "0.4")),
        web_search_provider=os.getenv("WEB_SEARCH_PROVIDER", "duckduckgo"),
        cors_origins=os.getenv("CORS_ORIGINS", ""),
        alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY", ""),
        cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
        rate_limit_min_interval=float(os.getenv("RATE_LIMIT_MIN_INTERVAL", "0.5")),
        sec_user_agent=os.getenv("SEC_USER_AGENT", ""),
        citadel_refresh_interval_seconds=int(os.getenv("CITADEL_REFRESH_INTERVAL_SECONDS", "21600")),
        openfigi_api_key=os.getenv("OPENFIGI_API_KEY", ""),
        gdelt_max_records=int(os.getenv("GDELT_MAX_RECORDS", "8")),
    )
