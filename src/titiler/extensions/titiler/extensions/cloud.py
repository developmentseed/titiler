from dataclasses import dataclass

from titiler.core import BaseTilerFactory
from titiler.core.factory import FactoryExtension


@dataclass
class cloudCredentialsExtension(FactoryExtension):
    """Add Cloud Credentials supports to rio-tiler"""
    import os
    google_application_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    def register(self, factory: "BaseTilerFactory"):
        if cloudCredentialsExtension.google_application_credentials:
            from typing import Dict
            env_dep = factory.environment_dependency
            def environment_dependency() -> Dict:
                environ = env_dep()
                environ.update(
                    {"GOOGLE_APPLICATION_CREDENTIALS": cloudCredentialsExtension.google_application_credentials}
                )
                return environ
            factory.environment_dependency = environment_dependency
        else:
            pass
