from dataclasses import dataclass

from titiler.core import BaseTilerFactory
from titiler.core.factory import FactoryExtension


@dataclass
class cloudCredentialsExtension(FactoryExtension):
    """Add Cloud Credentials supports to rio-tiler"""

    def register(self, factory: "BaseTilerFactory"):
        from google.auth.exceptions import DefaultCredentialsError
        import google.auth
        try:
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/devstorage.read_only"])
        except google.auth.exceptions.DefaultCredentialsError:
            credentials = None
        if credentials:
            from google.auth.transport.requests import Request
            env_dep = factory.environment_dependency
            request = Request()
            import rasterio
            major_version, minor_version, _ = rasterio.__gdal_version__.split('.')
            from typing import Callable
            refresh_token_callable: Callable
            update_environ_callable: Callable
            if int(major_version) >= 3 and int(minor_version) >= 7:
                def refresh_token():
                    credentials.refresh(request)
                refresh_token_callable = refresh_token
                def update_environ(environ: dict):
                    environ["GDAL_HTTP_HEADERS"] = f"Authorization: Bearer {credentials.token}"
                update_environ_callable = update_environ
            else:
                import tempfile
                header_file: tempfile.NamedTemporaryFile = tempfile.NamedTemporaryFile("wt")
                def refresh_token():
                    credentials.refresh(request)
                    header_file.truncate(0)
                    header_file.write(f"Authorization: Bearer {credentials.token}")
                    header_file.flush()
                refresh_token_callable = refresh_token
                def update_environ(environ: dict):
                    environ["GDAL_HTTP_HEADER_FILE"] = header_file.name
                update_environ_callable = update_environ

            from typing import Dict

            def environment_dependency() -> Dict:
                if not credentials.valid:
                    refresh_token_callable()
                environ = env_dep()
                update_environ_callable(environ)
                return environ
            factory.environment_dependency = environment_dependency
        else:
            pass
