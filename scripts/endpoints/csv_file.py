import io
import json
import zipfile
from typing import Annotated, Dict, Optional

from fastapi import Depends, UploadFile, File, HTTPException
from starlette.responses import StreamingResponse

from scripts.endpoints.proceed import WeatherTable
from scripts.shared.user import get_current_user
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
):
    csv = await CSVFile.filter(user=await get_current_user(user))
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


# assign_csvs
async def proceed_csv(user: Annotated[Dict, Depends(permission_setter())], id: str, ):
    async def create_table(_type: str, csv: CSVFile):
        _table = await CSVFile.create(
            name=meta.name,
            latitude=meta.latitude,
            longitude=meta.longitude,
            type=_type,
            description=meta.description,
            user=await get_current_user(user),
            csv_file_id=f"{csv}"
        )
        return _table

    try:
        meta = (await CSVFile.filter(user=await get_current_user(user), id=id))[0]
        table = WeatherTable(path_io=f'data/csv/{meta.id}.csv')
        table.load()

        ky = await create_table("proceed_data_Ky", csv=meta.id)
        ed = await create_table("proceed_data_Ed", csv=meta.id)
        em = await create_table("proceed_data_Em", csv=meta.id)
        gtk = await create_table("proceed_data_GTK", csv=meta.id)
        mean_t_months = await create_table('proceed_data_mean_t_months', csv=meta.id)
        active_months = await create_table('proceed_data_active_months', csv=meta.id)
        decades_grouped = await create_table("proceed_data_decades_grouped", csv=meta.id)
        em_active_months = await create_table('proceed_em_active_months', csv=meta.id)
        grouped_year = await create_table('groups_year', csv=meta.id)

        table.ky.to_csv(f'data/csv/{ky.id}.csv')
        table.em.to_csv(f'data/csv/{em.id}.csv')
        table.ed.to_csv(f'data/csv/{ed.id}.csv')
        table.gtk.to_csv(f'data/csv/{gtk.id}.csv')
        table.decades_grouped.to_csv(f'data/csv/{decades_grouped.id}.csv')
        table.active_months.to_csv(f'data/csv/{active_months.id}.csv')
        table.mean_t_months.to_csv(f'data/csv/{mean_t_months.id}.csv')
        table.em_active_months.to_csv(f'data/csv/{em_active_months.id}.csv')
        table.groupby_year.to_csv(f'data/csv/{grouped_year.id}.csv')

    except Exception as e:
        raise HTTPException(422, f"Unprocessable file {e}")
    return [
        ky,
        ed,
        em,
        gtk,
        mean_t_months,
        active_months,
        decades_grouped,
        em_active_months,
        grouped_year,
    ]


async def get_proceed(user: Annotated[Dict, Depends(permission_setter())], id: str, ) -> StreamingResponse:
    try:
        tables = await CSVFile.filter(user=await get_current_user(user), csv_file_id=id)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for table in tables:
                csv = PandasTable(path_io=f'data/csv/{table.id}.csv')
                csv.load()
                csv_buffer = io.BytesIO()
                csv.data.to_csv(csv_buffer, index=False)
                csv_buffer.seek(0)
                zip_file.writestr(f'{table.date_created}_{table.id}_{table.type}.csv', csv_buffer.getvalue())
        zip_buffer.seek(0)
        headers = {
            'Content-Disposition': f'attachment; filename="{id}.zip"'
        }
        return StreamingResponse(zip_buffer, headers=headers)

    except Exception as e:
        raise HTTPException(403, f'{e}')


async def assign_tables_to_map(user: Annotated[Dict, Depends(permission_setter())], map_id: str, csv_ids: list[str]):
    user = await get_current_user(user)
    return await CSVFile.filter(user=user, csv_file_id__in=csv_ids).update(map_id=map_id)

