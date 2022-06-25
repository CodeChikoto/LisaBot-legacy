from typing import Dict, List, Optional
from peewee import *
from environs import Env

env = Env()
env.read_env()

mai_database = MySQLDatabase('maimai', **{'charset': 'utf8mb4', 'sql_mode': 'PIPES_AS_CONCAT', 'use_unicode': True,
                                          'host': '127.0.0.1', 'port': 3306, 'user': 'anyone',
                                          'password': 'UnpublicData'})


class UnknownField(object):
    def __init__(self, *_, **__): pass


class MaiModel(Model):
    class Meta:
        database = mai_database


class ChartDifficulty(MaiModel):
    difficulty = CharField(column_name='Difficulty')
    id = IntegerField(column_name='Id')
    inner_level = FloatField(column_name='InnerLevel')
    level = CharField(column_name='Level')
    version = CharField(column_name='Version')

    class Meta:
        table_name = 'ChartDifficulty'
        indexes = (
            (('id', 'difficulty', 'version'), True),
        )
        primary_key = CompositeKey('difficulty', 'id', 'version')


class ChartInfo(MaiModel):
    break_ = IntegerField(column_name='Break')
    charter = CharField(column_name='Charter')
    difficulty = CharField(column_name='Difficulty')
    hold = IntegerField(column_name='Hold')
    id = IntegerField(column_name='Id')
    plate_mask = BitField(column_name='PlateMask', null=True)
    slide = IntegerField(column_name='Slide')
    tap = IntegerField(column_name='Tap')
    touch = IntegerField(column_name='Touch', null=True)

    class Meta:
        table_name = 'ChartInfo'
        indexes = ((('id', 'difficulty'), True), )
        primary_key = CompositeKey('difficulty', 'id')


class SongAlias(MaiModel):
    alias = CharField(column_name='Alias')
    id = IntegerField(column_name='Id')

    class Meta:
        table_name = 'SongAlias'
        primary_key = False


class SongInfo(MaiModel):
    artist = CharField(column_name='Artist')
    bpm = IntegerField(column_name='BPM')
    chart_type = CharField(column_name='ChartType')
    china_version = CharField(column_name='ChinaVersion', null=True)
    cover = BlobField(column_name='Cover', null=True)
    genre = CharField(column_name='Genre')
    id = IntegerField(column_name='Id', primary_key=True)
    title = CharField(column_name='Title')
    version = CharField(column_name='Version')

    class Meta:
        table_name = 'SongInfo'


class Store(MaiModel):
    address = CharField(column_name='Address')
    city = CharField(column_name='City')
    close_time = TimeField(column_name='CloseTime', null=True)
    coin_per_play = IntegerField(column_name='CoinPerPlay', null=True)
    coin_price = FloatField(column_name='CoinPrice', null=True)
    machine_amount = IntegerField(column_name='MachineAmount', null=True)
    mid_price = FloatField(column_name='MidPrice', null=True)
    name = CharField(column_name='Name')
    note = CharField(column_name='Note', null=True)
    province = CharField(column_name='Province')
    start_time = TimeField(column_name='StartTime', null=True)
    id = CharField(primary_key=True)

    class Meta:
        table_name = 'Store'


class PlateInfo(MaiModel):
    plate_id = CharField(column_name="PlateId", primary_key=True)
    plate_name = CharField(column_name="PlateName")
    customizable = BooleanField(column_name="Customizable")
    version_no = IntegerField(column_name="VersionNo")
    requirement = TextField(column_name="Requirement")
    image = BlobField(column_name="Image")
    enable = BooleanField(column_name="Enable")
    version_mask = BitField(column_name="VersionMask")

    class Meta:
        table_name = 'PlateInfo'
