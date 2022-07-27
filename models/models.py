from playhouse.mysql_ext import MySQLConnectorDatabase
from playhouse.shortcuts import ReconnectMixin


class ReconnectMySQLDatabase(ReconnectMixin, MySQLConnectorDatabase):
    pass