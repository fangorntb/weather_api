from tortoise import models, fields

from scripts.models.enums import CsvTypes


class User(models.Model):
    name = fields.TextField(pk=True)
    scopes = fields.JSONField()
    pass_hash = fields.TextField()


class Map(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    description = fields.TextField()
    date_created = fields.DatetimeField(auto_now=True)
    user = fields.ForeignKeyField('pg.User')


class CSVFile(models.Model):
    id = fields.UUIDField(pk=True)
    name = fields.TextField()
    latitude = fields.FloatField()
    longitude = fields.FloatField()
    type = fields.CharEnumField(CsvTypes)

    description = fields.TextField()

    date_created = fields.DatetimeField(auto_now=True)
    user = fields.ForeignKeyField('pg.User')


# class MapCSVFile(models.Model):
#     id = fields.UUIDField(pk=True)
#     map = fields.ForeignKeyField('pg.Map')
#     csvfile = fields.ForeignKeyField('pg.CSVFile')
