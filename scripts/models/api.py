from pydantic import BaseModel
from tortoise.contrib.pydantic import pydantic_model_creator

from scripts.models.pg import Map, CSVFile


class Token(BaseModel):
    access_token: str
    token_type: str


MapReqPyd = pydantic_model_creator(Map, exclude=('id', 'user_id', 'date_created'), )
MapRespPyd = pydantic_model_creator(Map, include=('id', 'user_id', 'date_created', 'description', 'name'))
CSVFileReqPyd = pydantic_model_creator(CSVFile, exclude=('id', 'user_id', 'date_created'), )
CSVFileRespPyd = pydantic_model_creator(
    CSVFile,
    include=('id', 'user_id', 'date_created', 'latitude', 'longitude', 'type', 'description'),
)
