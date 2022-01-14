import pymysql
from typing import *
from dbutils.pooled_db import PooledDB


database_pool = PooledDB(creator=pymysql, maxconnections=490, mincached=5, maxcached=None, blocking=True,
                         maxusage=None, ping=4, host="127.0.0.1", port=3306, user="root", password="Root-User",
                         database="maimai", charset="utf8")
