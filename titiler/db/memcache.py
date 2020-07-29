"""titiler.cache.memcache: memcached layer."""
from typing import Optional, Tuple

from bmemcached import Client

from titiler import settings
from titiler.ressources.enums import ImageType


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
        """Init Cache Layer."""
        self.client = Client((f"{host}:{port}",), user, password)

    def get_image_from_cache(self, img_hash: str) -> Tuple[bytes, ImageType]:
        """
        Get image body from cache layer.

        Attributes
        ----------
            img_hash : str
                file url.

        Returns
        -------
            img : bytes
                image body.
            ext : str
                image ext

        """
        content, ext = self.client.get(img_hash)
        return content, ext

    def set_image_cache(
        self, img_hash: str, body: Tuple[bytes, ImageType], timeout: int = 432000
    ) -> bool:
        """
        Set base64 encoded image body in cache layer.

        Attributes
        ----------
            img_hash : str
                file url.
            body : tuple
                image body + ext
        Returns
        -------
            bool

        """
        try:
            return self.client.set(img_hash, body, time=timeout)
        except Exception:
            return False
