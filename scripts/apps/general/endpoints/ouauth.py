from fastapi import HTTPException, Depends
from starlette import status
from hashlib import sha1
from scripts.shared.security import OAuth2Form, APP_NAME, create_access_token, RegisterForm
from scripts.models.pg import User


def encode_pass(p: str):
    return sha1(p.encode(), usedforsecurity=True).hexdigest()


async def login_for_token(form_data: OAuth2Form = Depends()):
    users = await User.filter(name=form_data.username, pass_hash=encode_pass(form_data.password))
    if not users.__len__():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid username or password'
        )
    token_data = {'issuer': APP_NAME, 'username': form_data.username, 'scopes': ' '.join(users[0].scopes)}
    access_token = create_access_token(token_data)
    return {'access_token': access_token, 'token_type': 'bearer'}


async def register(form_data: RegisterForm = Depends()):
    await User.create(name=form_data.username, pass_hash=encode_pass(form_data.password), scopes=form_data.scopes)
    token_data = {'issuer': APP_NAME, 'username': form_data.username, 'scopes': ' '.join(form_data.scopes)}
    access_token = create_access_token(token_data)
    return {'access_token': access_token, 'token_type': 'bearer'}