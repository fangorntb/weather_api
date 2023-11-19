import json
from typing import Annotated, Dict, Optional

from fastapi import Depends, UploadFile, File, HTTPException

from scripts.apps.general.shared.user import get_current_user
from scripts.models.api import CSVFileReqPyd
from scripts.models.pg import CSVFile
from scripts.shared.lab_tools import PandasTable
from scripts.shared.security import permission_setter


async def load_csv_file(
        user: Annotated[Dict, Depends(permission_setter())],
        metadata: CSVFileReqPyd = Depends(),
        data: UploadFile = File(...)
):
    try:
        table = PandasTable(path_io=data.file)
        table.load()
    except Exception as e:
        raise HTTPException(422, f"Unprocessable file {e}")
    meta = await CSVFile.create(**metadata.dict(), user=await get_current_user(user))
    table.path_io = f'data/csv/{meta.id}.csv'
    table.save()
    return meta


async def get_csv_metas(
        user: Annotated[Dict, Depends(permission_setter())],
        offset: int = 0,
):
    csv = await CSVFile.filter(user=await get_current_user(user)).offset(offset)
    return csv


async def get_csv_json(
        user: Annotated[Dict, Depends(permission_setter())],
        id: str,
        head: Optional[int] = 5
):
    try:
        meta = (await CSVFile.filter(user=await get_current_user(user), id=id))[0]
        table = PandasTable(path_io=f'data/csv/{meta.id}.csv')
        table.load()
    except Exception as e:
        raise HTTPException(403, f'{e}')
    table = json.loads(table.data.to_json(orient='records'))
    return {'table_data': (table if head is None else table[:head]), 'meta': meta.__dict__}
