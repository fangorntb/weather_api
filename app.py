import asyncio

from dotenv import load_dotenv
from tortoise.contrib.fastapi import register_tortoise
from uvicorn import Server, Config

from scripts.app import API

load_dotenv('configs/.main.env')

register_tortoise(
    API,
    db_url='postgres://docker:docker@localhost:5432/docker',
    modules={"pg": ['scripts.models.pg']},
    generate_schemas=True,
)


if __name__ == '__main__':
    asyncio.run(Server(Config(API, port=8090),).serve())
