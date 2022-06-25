from peewee import *
from environs import Env

env = Env()
env.read_env()

player_database = MySQLDatabase('Player', **{'charset': 'utf8', 'sql_mode': 'PIPES_AS_CONCAT', 'use_unicode': True,
                                             'host': '154.86.19.207', 'port': 3306, 'user': 'koto',
                                             'password': 'ConnectionsFromKoto'})


class PlayerModel(Model):
    class Meta:
        database = player_database


class PlayerBasicInfo(PlayerModel):
    user_id = AutoField(column_name="UserId", primary_key=True)
    username = CharField(column_name="Username")
    password = CharField(column_name="Password")
    qq_id = CharField(column_name="QQId")
    nickname = CharField(column_name="Nickname")
    plate_id = CharField(column_name="PlateId")
    rank_no = SmallIntegerField(column_name="RankNo")
    rank_rating = SmallIntegerField(column_name="RankRating")
    rating = SmallIntegerField(column_name="Rating")
    ano_rating = SmallIntegerField(column_name="AnoRating")
    play_count = IntegerField(column_name="PlayCount")
    update_time = DateTimeField(column_name="UpdateTime")

    class Meta:
        table_name = "BasicInfo"


class PlayerPlate(PlayerModel):
    user_id = IntegerField(column_name="UserId")
    plate_id = CharField(column_name="PlateId")

    class Meta:
        table_name = "PlayerPlate"
        primary_key = None


class PlayerRecord(PlayerModel):
    user_id = IntegerField(column_name='UserId')
    song_id = IntegerField(column_name='SongId')
    difficulty = CharField(column_name='Difficulty')
    achievements = FloatField(column_name="Achievements")
    achi_rank = CharField(column_name="AchiRank")
    single_rating = SmallIntegerField(column_name="SingleRating")
    ano_single_rating = SmallIntegerField(column_name="AnoSingleRating")
    dx_score = IntegerField(column_name="DXScore")
    star = SmallIntegerField(column_name="Star")
    sync = CharField(column_name="Sync")
    combo = CharField(column_name="Combo")

    class Meta:
        table_name = "Record"
        primary_key = CompositeKey('user_id', 'song_id', 'difficulty')


class BestRecord(PlayerModel):
    user_id = IntegerField(column_name="UserId")
    song_id = SmallIntegerField(column_name="SongId")
    title = CharField(column_name="Title")
    chart_type = CharField(column_name="ChartType")
    difficulty = CharField(column_name="Difficulty")
    level = CharField(column_name="Level")
    inner_level = FloatField(column_name="InnerLevel")
    achievements = FloatField(column_name="Achievements")
    achi_rank = CharField(column_name="AchiRank")
    single_rating = SmallIntegerField(column_name="SingleRating")
    combo = CharField(column_name="Combo")
    sync = CharField(column_name="Sync")
    dx_score = IntegerField(column_name="DXScore")
    star = SmallIntegerField(column_name="Star")
    plate_mask = BitField(column_name="PlateMask")

    class Meta:
        indexes = ((('user_id', 'song_id', 'difficulty'), True),)
        primary_key = None


class B40Record(BestRecord):
    class Meta:
        table_name = 'B40Record'


class B50Record(BestRecord):
    class Meta:
        table_name = 'B50Record'


class UserBindWithQQIdRecord(PlayerModel):
    user_id = IntegerField(column_name="UserId")
    qq_id = IntegerField(column_name="QQId")
    verification_code = CharField(column_name="VerificationCode")
    expire_time = DateTimeField(column_name="ExpireTime")


class PlateSetting(PlayerModel):
    qq_id = IntegerField(column_name="QQId", primary_key=True)
    plate_id = CharField(column_name="PlateId")

    class Meta:
        table_name = "PlateSetting"


class BlackList(PlayerModel):
    qq_id = IntegerField(column_name="QQId", primary_key=True)

    class Meta:
        table_name = "Blacklist"
