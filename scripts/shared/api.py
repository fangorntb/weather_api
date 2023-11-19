import dataclasses
import time
from inspect import isfunction
from os import PathLike
from typing import (
    List,
    Optional,
    Union,
    Callable,
    Dict, Iterable
)

from fastapi import FastAPI, APIRouter
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.staticfiles import StaticFiles


def get_path(include: bool, path: str, ) -> str:
    return f"{'/api' if include else ''}/{path}".rstrip('/')


class Router:
    def __init__(
            self,
            method: str,
            path: str,
            endpoint: Callable = lambda _: _,
            description: Optional[str] = None,
            include: bool = True,
            responses: Dict = None,
            **kwargs
    ):
        self.router = APIRouter(**kwargs)
        self.router.__getattribute__(method.lower())(
            path=get_path(include, path),
            description=description,
            include_in_schema=include,
            responses=responses,
        )(endpoint)

    def __repr__(self) -> str:
        return self.router.__repr__()

    def include_router(self, router: Union[APIRouter, 'Router']) -> None:
        self.router.include_router(router if router else Router)


class RootRouter:
    def __init__(
            self,
            method: str,
            path: str,
            endpoint: Callable = lambda _: _,
            include: bool = False,
            **kwargs
    ):
        self.method = method.lower()
        self.path = get_path(include, path)
        self.endpoint = endpoint
        self.kwargs = kwargs
        self.include = include


class Group(APIRouter):
    def __init__(self, *routes: Router, tags: Optional[List[str]] = None, **kwargs):
        super().__init__(tags=tags, **kwargs)
        include_routers(self, *map(lambda x: x.router, routes))

    def __repr__(self):
        return f'{self.routes}'


def include_routers(
        node: Union[APIRouter, FastAPI, Router, RootRouter],
        *routers: APIRouter,
) -> Union[APIRouter, FastAPI, Router]:
    for router in filter(lambda x: isinstance(x, RootRouter), routers):
        router: RootRouter
        node.__getattribute__(router.method.lower())(
            router.path,
            include_in_schema=router.include, **router.kwargs,
        )(router.endpoint)
    for router in filter(lambda x: not isinstance(x, RootRouter), routers):
        router: APIRouter | Router
        node.include_router(router if isinstance(router, APIRouter) else router.router)
    return node


@dataclasses.dataclass
class Mount:
    path: str
    static: StaticFiles
    name: str


def get_app(
        *routers: Union[APIRouter, Router | RootRouter],
        middlewares: Optional[List[callable]] = None,
        mount: Iterable[Mount] = None,
        openapi_kwargs: Dict = None,
        **conf,
):
    _app = FastAPI(**conf)
    mount_static(_app, mount)
    add_middlewares(_app, middlewares, 'middleware', lambda x: isfunction(x), ('http',), ('https',))
    add_middlewares(_app, middlewares, 'add_middleware', lambda x: not isfunction(x), )
    include_routers(_app, *routers)
    if openapi_kwargs is not None:
        _app.openapi_schema = custom_openapi(_app, **openapi_kwargs)
    return _app


def mount_static(_app: FastAPI, mount: Iterable[Mount] = None, ):
    return tuple(map(lambda x: _app.mount(x.path, x.static, name=x.name), mount)) if mount is not None else ...


def add_middlewares(_app, middlewares, tpe: str, fil: callable, *args):
    middlewares = filter(fil, middlewares)
    if args.__len__():
        for sample_args in args:
            tuple(
                map(
                    _app.__getattribute__(tpe)(*sample_args), middlewares)
            ) if middlewares is not None else ...
    else:
        tuple(
            map(
                _app.__getattribute__(tpe), middlewares)
        ) if middlewares is not None else ...


def favicon_endpoint(favicon_path: Union[str, PathLike]) -> Callable:
    async def favicon():
        return FileResponse(favicon_path)

    return favicon


def swagger(title: str, favicon_url: str, **kwargs):
    async def swagger_ui():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=title,
            swagger_favicon_url=favicon_url,
            **kwargs,
        )

    return swagger_ui


async def process_time_middleware(request: Request, call_next: callable) -> Response:
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


def custom_openapi(app: FastAPI, logo_url: str = None, **kwargs):
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        routes=app.routes,
        **kwargs
    )
    openapi_schema["info"]["x-logo"] = {
        "url": logo_url
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema
