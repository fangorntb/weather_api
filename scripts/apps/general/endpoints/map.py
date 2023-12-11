import io
import zipfile
from typing import Annotated, Dict

import folium
import pandas as pd
from fastapi import Depends
from folium.plugins import HeatMap, MarkerCluster
from starlette.responses import StreamingResponse

from scripts.apps.general.shared.user import get_current_user
from scripts.models.api import MapReqPyd
from scripts.models.enums import CsvTypes
from scripts.models.pg import Map, CSVFile
from scripts.shared.lab_tools import PandasTable
from scripts.shared.security import permission_setter


async def create_map(data: MapReqPyd, user: Annotated[Dict, Depends(permission_setter())]):
    return await Map.create(**data.dict(), user=await get_current_user(user))


async def get_maps_meta(user: Annotated[Dict, Depends(permission_setter())],):
    return await Map.filter(user=await get_current_user(user)).order_by('date_created')


def visualize_map(df, year, io):
    data_year = df[df['DATE'] == year]
    map_center = [data_year['latitude'].mean(), data_year['longitude'].mean()]
    my_map = folium.Map(location=map_center, zoom_start=2)
    heat_data = [[row['latitude'], row['longitude'], row['T2M']] for index, row in data_year.iterrows()]
    HeatMap(heat_data, name='T2M', blur=16).add_to(my_map)
    marker_cluster = MarkerCluster(name='PRECTOTCORR').add_to(my_map)
    for index, row in data_year.iterrows():
        folium.CircleMarker(
            location=[row['latitude'], row['longitude']],
            radius=(row['PRECTOTCORR'] - data_year['PRECTOTCORR'].mean()) / 10,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=1,
            tooltip=row['name']
        ).add_to(marker_cluster)

    folium.LayerControl().add_to(my_map)

    my_map.save(io, close_file=False)


async def proceed_maps(user: Annotated[Dict, Depends(permission_setter())], map_id: str, ):
    user = await get_current_user(user)
    tables = await CSVFile.filter(user=user, map_id=map_id, type=CsvTypes.groups_year)
    main_table = (await CSVFile.filter(id__in=list(map(lambda x: x.csv_file_id, tables))))[0]

    latitude = main_table.latitude
    longitude = main_table.longitude
    df_lst = []
    name = main_table.name
    for table in tables:
        csv = PandasTable(path_io=f'data/csv/{table.id}.csv')
        csv.load()
        csv['name'] = name
        csv['latitude'] = latitude
        csv['longitude'] = longitude
        df_lst.append(csv)

    df = pd.concat([i.data for i in df_lst])
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for year in df['DATE'].tolist():
            buffer = io.BytesIO()
            visualize_map(df, year=year, io=buffer)
            buffer.seek(0)

            zip_file.writestr(f'{year}.html', buffer.getvalue())
    zip_buffer.seek(0)
    headers = {
        'Content-Disposition': f'attachment; filename="{map_id}.zip"'
    }
    return StreamingResponse(zip_buffer, headers=headers)
