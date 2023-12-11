from pathlib import Path

from starlette.staticfiles import StaticFiles

from scripts.apps.general.endpoints.map import create_map, get_maps_meta, proceed_maps
from scripts.apps.general.endpoints.csv_file import get_csv_metas, load_csv_file, get_csv_json, proceed_csv, \
    get_proceed, assign_tables_to_map

from scripts.apps.general.endpoints.ouauth import login_for_token, register
from scripts.shared.api import (
    Router,
    Group,
    get_app,
    favicon_endpoint,
    process_time_middleware,
    Mount,
)

# get_csv_metas
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
        Router('post', 'assign_tables_to_map', assign_tables_to_map, include=True),
        Router('post', 'proceed_maps', proceed_maps, include=True),
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