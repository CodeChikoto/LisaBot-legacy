from peewee import *
from environs import Env

env = Env()
env.read_env()

quotations_database = MySQLDatabase('Quotations',
                                    **{'charset': 'utf8', 'sql_mode': 'PIPES_AS_CONCAT', 'use_unicode': True,
                                       'host': '127.0.0.1', 'port': 3306, 'user': 'anyone',
                                       'password': 'UnpublicData'})


class Quotations(Model):
    class Meta:
        database = quotations_database


class Emoji(Quotations):
    id = IntegerField(column_name="Id", primary_key=True)
    type_ = CharField(column_name="Type")
    image = BlobField(column_name="Image")
    bot_name = CharField(column_name="BotName")

    class Meta:
        table_name = "Emoji"
