from typing import Annotated, Dict, List

from fastapi import Depends

from scripts.apps.general.shared.user import get_current_user
from scripts.models.api import MapReqPyd, MapRespPyd
from scripts.models.pg import Map
from scripts.shared.security import permission_setter


async def create_map(data: MapReqPyd, user: Annotated[Dict, Depends(permission_setter())]) -> MapRespPyd:
    return await Map.create(**data.dict(), user=await get_current_user(user))


async def get_maps_meta(user: Annotated[Dict, Depends(permission_setter())], offset: int) -> List[MapRespPyd]:
    return await Map.filter(user=await get_current_user(user)).order_by('date_created').offset(offset)

