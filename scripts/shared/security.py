import datetime
from typing import Iterable
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.param_functions import Form
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from jose import jwt
from pydantic import BaseModel

APP_NAME = 'myapp'

TOKEN_SECRET = 'YOUR TOKEN SECRET HERE'

ALGORITHM = 'HS256'


class OAuth2Form:
    def __init__(
            self,
            username: str = Form(),
            password: str = Form(),
    ):
        self.username = username
        self.password = password


class RegisterForm(OAuth2Form):
    def __init__(self, username: str = Form(), password: str = Form(), scopes: list[str] = Form([])):
        super().__init__(username, password)
        self.username = username
        self.password = password
        self.scopes = scopes


def create_access_token(
        data: dict,
        expiry_seconds: Optional[int] = 60 * 60 * 24 * 7  # one week, in seconds
) -> str:
    to_encode = data.copy()
    expiry_date = datetime.datetime.utcnow() + datetime.timedelta(seconds=expiry_seconds)
    to_encode.update({'expires_at': expiry_date.timestamp()})
    encoded_jwt = jwt.encode(to_encode, TOKEN_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def validate_token(token: dict) -> bool:
    """ensure the token is valid (i.e. issued by us and not expired)
    """
    return token.get('issuer') == APP_NAME and token.get('expires_at', 0) > datetime.datetime.utcnow().timestamp()


def permission_setter(*scopes: str) -> callable:

    async def ensure_permissions(
            security_scopes: SecurityScopes,
            token: str = Depends(
                OAuth2PasswordBearer(
                    tokenUrl="/api/token",
                )
            ),
    ):
        decoded_token = jwt.decode(token, TOKEN_SECRET, algorithms=[ALGORITHM])
        if not scopes.__len__():
            return decoded_token
        elif not validate_token(decoded_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate credentials'
            )

        # check if the provided token has any of the necessary scopes
        elif not has_any_scope(scopes, decoded_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Insufficient permissions'
            )
        return decoded_token

    return ensure_permissions


def has_any_scope(scopes: Iterable[str], token_data: dict) -> bool:
    if not scopes:
        return True
    return any(scope in scopes for scope in token_data.get('scopes', '').split())


def validate_login(username: str, password: str, func: callable = lambda x, y: True) -> bool:
    return func(username, password)


class TokenData(BaseModel):
    username: str | None = None
