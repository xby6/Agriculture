import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv


@dataclass
class GatewaySettings:
    cloud_0531_base_url: str = 'http://www.0531yun.com'
    cloud_0531_login_name: str = ''
    cloud_0531_password: str = ''
    cloud_0531_group_id: str = ''
    cloud_0531_poll_seconds: int = 600
    cloud_0531_timeout_seconds: int = 15
    agri_backend_url: str = 'http://127.0.0.1:9099'
    agri_internal_api_key: str = ''


@lru_cache
def get_settings() -> GatewaySettings:
    load_dotenv()
    return GatewaySettings(
        cloud_0531_base_url=os.getenv('CLOUD_0531_BASE_URL', 'http://www.0531yun.com'),
        cloud_0531_login_name=os.getenv('CLOUD_0531_LOGIN_NAME', ''),
        cloud_0531_password=os.getenv('CLOUD_0531_PASSWORD', ''),
        cloud_0531_group_id=os.getenv('CLOUD_0531_GROUP_ID', ''),
        cloud_0531_poll_seconds=_int_env('CLOUD_0531_POLL_SECONDS', 600),
        cloud_0531_timeout_seconds=_int_env('CLOUD_0531_TIMEOUT_SECONDS', 15),
        agri_backend_url=os.getenv('AGRI_BACKEND_URL', 'http://127.0.0.1:9099'),
        agri_internal_api_key=os.getenv('AGRI_INTERNAL_API_KEY', ''),
    )


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, default))
    except (TypeError, ValueError):
        return default
