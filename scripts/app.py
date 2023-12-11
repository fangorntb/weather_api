# get_csv_metas
from pathlib import Path

from starlette.staticfiles import StaticFiles

from scripts.endpoints.csv_file import (
    assign_tables_to_map,
    load_csv_file,
    get_csv_metas,
    get_csv_json,
    proceed_csv,
    get_proceed,
)
from scripts.endpoints.map import get_maps_meta, create_map, proceed_maps
from scripts.endpoints.ouauth import login_for_token, register
from scripts.shared.api import (
    get_app,
    Group,
    Router,
    favicon_endpoint,
    Mount,
    process_time_middleware,
)

API = get_app(
    Router('get', 'favicon.ico', favicon_endpoint('static/favicon-32x32.png'), include=False),
    Group(
        Router('post', 'token', login_for_token, include=True),
        Router('post', 'register', register, include=True),
        tags=['ouauth2']
    ),
    Group(
        Router('get', 'maps', get_maps_meta, include=True),
        Router('post', 'map', create_map, include=True),
        Router('post', 'map/assign', assign_tables_to_map, include=True),
        Router('post', 'map/assign/get', proceed_maps, include=True),
        tags=['map']
    ),
    Group(
        Router('post', 'csv', load_csv_file, include=True),
        Router('get', 'csvs', get_csv_metas, include=True),
        Router('get', 'csv/json', get_csv_json, include=True),
        Router('post', 'csv/proceed', proceed_csv, include=True),
        Router('get', 'csv/proceed-zip', get_proceed, include=True),
        tags=['csv']
    ),
    mount=[
        Mount(str(Path.cwd() / 'data'), StaticFiles(directory='data'), 'data'),
        Mount(str(Path.cwd() / 'static'), StaticFiles(directory='static'), 'static')
    ],
    middlewares=[process_time_middleware],
    openapi_kwargs={
        'title': 'Weather API',
        'version': '0.1',
        'logo_url': 'favicon.ico'
    },
    **{
        'docs_url': '/',
        'redoc_url': None,
        "swagger_ui_parameters": {"syntaxHighlight.theme": "obsidian"}
    },
)