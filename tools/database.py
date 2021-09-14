import pymysql
from typing import *
from threading import Thread


class Cursor():
    host, user, password, database, port = "", "", "", "", ""
    connection = None
    res = []

    def __init__(self, host="39.106.184.73", user="root",
                 password="Root-User", database="maimai", port=3306):
        self.host, self.user, self.password, self.database, self.port = \
            host, user, password, database, port
        self.connect()

    def connect(self):
        self.connection = pymysql.connect(host=self.host, user=self.user, password=self.password,
                                          db=self.database, port=self.port)

    def execute(self, arg: str):
        self.connection.ping(True)
        cursor = self.connection.cursor()
        amount = cursor.execute(arg)
        self.res = list(cursor.fetchall())
        cursor.close()
        return amount

    def fetchone(self):
        return self.res.pop(0) if self.res else []

    def fetchall(self):
        return self.res
