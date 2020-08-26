"""titiler.cache.memcache: memcached layer."""

from dataclasses import dataclass
from typing import Any, Optional, Tuple

from .. import settings

from fastapi.logger import logger

try:
    from bmemcached import Client
except ImportError:  # pragma: no cover

    @dataclass
    class Client:  # type: ignore
        """Fake Cache Client."""

        host: Tuple
        user: Optional[str]
        password: Optional[str]

        def get(self, *args, **kwargs):
            """get method."""
            raise NotImplementedError

        def set(self, *args, **kwargs):
            """set method."""
            pass

        def disconnect_all(self):
            """Disconnect."""
            pass

    logger.warning(
        "python-binary-memcached not installed, Cache won't be available.\n"
        "To install, run: pip install python-binary-memcached"
    )


class CacheLayer(object):
    """Memcache Wrapper."""

    @classmethod
    def create_from_env(cls) -> "CacheLayer":
        """
        Instatiate from environment variables.
        """
        return cls(
            host=settings.MEMCACHE_HOST,
            port=settings.MEMCACHE_PORT,
            user=settings.MEMCACHE_USERNAME,
            password=settings.MEMCACHE_PASSWORD,
        )

    def __init__(
        self,
        host,
        port: int = 11211,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """Create Cache Layer client."""
        self.client = Client((f"{host}:{port}",), user, password)

    def get(self, item_id: str) -> Any:
        """Get item from cache.

        Args:
            item_id: Cache items id.

        Returns:
            item body

        """
        return self.client.get(item_id)

    def set(self, item_id: str, body: Any, timeout: int = 432000) -> bool:
        """
        Set item in cache.

        Args:
            item_id: Cache items id.
            body: item body to store
            timeout: time to live limit

        Returns:
            bool: True if succeed

        """
        try:
            return self.client.set(item_id, body, time=timeout)
        except Exception:
            return False
