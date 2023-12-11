from fastapi import HTTPException
from typing import Dict

from scripts.models.pg import User


async def get_current_user(user: Dict):
    try:
        return (await User.filter(name=user.get('username')))[0]
    except Exception as e:
        raise HTTPException(401) from e