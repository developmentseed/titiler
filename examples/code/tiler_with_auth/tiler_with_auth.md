**Goal**: Add simple token auth

**requirements**: titiler.core, python-jose[cryptography]

Learn more about security over [FastAPI documentation](https://fastapi.tiangolo.com/tutorial/security/)

1 - Security settings (secret key)

```python
"""Security Settings.

app/settings.py

"""

from pydantic import BaseSettings


class AuthSettings(BaseSettings):
    """Application settings"""

    # Create secret key using `openssl rand -hex 32`
    # example: "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    secret: str
    expires: int = 3600
    algorithm: str = "HS256"

    class Config:
        """model config"""

        env_prefix = "SECURITY_"


auth_config = AuthSettings()
```

2 - Create a Token `Model`

```python
"""Models.

app/models.py

"""

from datetime import datetime, timedelta
from typing import List, Optional

from jose import jwt
from pydantic import BaseModel, Field, validator

from .settings import auth_config

# We add scopes - because we are fancy
availables_scopes = ["tiles:read"]


class AccessToken(BaseModel):
    """API Token info."""

    sub: str = Field(..., alias="username", regex="^[a-zA-Z0-9-_]{1,32}$")
    scope: List = ["tiles:read"]
    iat: Optional[datetime] = None
    exp: Optional[datetime] = None
    groups: Optional[List[str]]

    @validator("iat", pre=True, always=True)
    def set_creation_time(cls, v) -> datetime:
        """Set token creation time (iat)."""
        return datetime.utcnow()

    @validator("exp", always=True)
    def set_expiration_time(cls, v, values) -> datetime:
        """Set token expiration time (iat)."""
        return values["iat"] + timedelta(seconds=auth_config.expires)

    @validator("scope", each_item=True)
    def valid_scopes(cls, v, values):
        """Validate Scopes."""
        v = v.lower()
        if v not in availables_scopes:
            raise ValueError(f"Invalid scope: {v}")
        return v.lower()

    class Config:
        """Access Token Model config."""

        extra = "forbid"

    @property
    def username(self) -> str:
        """Return Username."""
        return self.sub

    def __str__(self):
        """Create jwt token string."""
        return jwt.encode(
            self.dict(exclude_none=True),
            auth_config.secret,
            algorithm=auth_config.algorithm,
        )

    @classmethod
    def from_string(cls, token: str):
        """Parse jwt token string."""
        res = jwt.decode(token, auth_config.secret, algorithms=[auth_config.algorithm])
        user = res.pop("sub")
        res["username"] = user
        return cls(**res)
```

3 - Create a custom `path dependency`

The `DatasetPathParams` will add 2 querystring parameter to our application:
- `url`: the dataset url (like in the regular titiler app)
- `access_token`: our `token` parameter

```python
"""Dependencies.

app/dependencies.py

"""

from jose import JWTError

from fastapi import HTTPException, Query, Security
from fastapi.security.api_key import APIKeyQuery

from .models import AccessToken

api_key_query = APIKeyQuery(name="access_token", auto_error=False)


# Custom Dataset Path dependency
def DatasetPathParams(
    url: str = Query(..., description="Dataset URL"),
    api_key_query: str = Security(api_key_query)
) -> str:
    """Create dataset path from args"""

    if not api_key_query:
        raise HTTPException(status_code=401, detail="Missing `access_token`")

    try:
        AccessToken.from_string(api_key_query)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid `access_token`")

    return url
```


3b - Create a Token creation/read endpoint (Optional)

```python
"""Tokens App.

app/tokens.py

"""

from typing import Any, Dict

from .models import AccessToken

from fastapi import APIRouter, Query

router = APIRouter()


@router.post(r"/create", responses={200: {"description": "Create a token"}})
def create_token(body: AccessToken):
    """create token."""
    return {"token": str(body)}


@router.get(r"/create", responses={200: {"description": "Create a token"}})
def get_token(
    username: str = Query(..., description="Username"),
    scope: str = Query(None, description="Coma (,) delimited token scopes"),
):
    """create token."""
    params: Dict[str, Any] = {"username": username}
    if scope:
        params["scope"] = scope.split(",")
    token = AccessToken(**params)
    return {"token": str(token)}
```

4 - Create the Tiler app with our custom `DatasetPathParams`

```python
"""app

app/main.py

"""

from titiler.core.factory import TilerFactory
from titiler.core.errors import DEFAULT_STATUS_CODES, add_exception_handlers

from fastapi import FastAPI

from .dependencies import DatasetPathParams

app = FastAPI(title="My simple app with auth")

# here we create a custom Tiler with out custom DatasetPathParams function
cog = TilerFactory(path_dependency=DatasetPathParams)
app.include_router(cog.router, tags=["Cloud Optimized GeoTIFF"])

# optional
from . import tokens
app.include_router(tokens.router)

add_exception_handlers(app, DEFAULT_STATUS_CODES)
```
