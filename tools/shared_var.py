from functools import lru_cache
import pymysql
import multiprocessing
from dbutils.pooled_db import PooledDB
import time

difficulty_alias = {
    "bas": "Basic",
    "bsc": "Basic",
    "绿": "Basic",
    "basic": "Basic",
    "adv": "Advanced",
    "黄": "Advanced",
    "advanced": "Advanced",
    "exp": "Expert",
    "ex": "Expert",
    "红": "Expert",
    "expert": "Expert",
    "mas": "Master",
    "mst": "Master",
    "紫": "Master",
    "master": "Master",
    "rem": "Re:MASTER",
    "re:m": "Re:MASTER",
    "白": "Re:MASTER",
    "re:master": "Re:MASTER",
    "remaster": "Re:MASTER",
    "": ""
}
difficulty_short = {0: "BSC", 1: "ADV", 2: "EXP", 3: "MST", 4: "REM", "Basic": "BSC", "Advanced": "ADV",
                    "Expert": "EXP", "Master": "MST", "Re:MASTER": "REM"}
difficulty_file = {"Basic": "BSC", "Advanced": "ADV", "Expert": "EXP", "Master": "MST", "Re:MASTER": "MST_Re"}
chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")([0-9]+)"
difficulty_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")"

# [0] match Koto's database (JapanVer), [1] match Koto's database (ChinaVer), [2] match diving-fish databse, [3]
version_alias = {'真': [['maimai', 'maimaiPLUS'], ['maimai', 'maimaiPLUS'], ['maimai', 'maimai PLUS'], 1 << 0],
                 '超': [['GreeN'], ['GreeN'], ['maimai GreeN'], 1 << 1],
                 '檄': [['GreeNPLUS'], ['GreeNPLUS'], ['maimai GreeN PLUS'], 1 << 2],
                 '橙': [['ORANGE'], ['ORANGE'], ['maimai ORANGE'], 1 << 3],
                 '暁': [['ORANGEPLUS'], ['ORANGEPLUS'], ['maimai ORANGE PLUS'], 1 << 4],
                 '晓': [['ORANGEPLUS'], ['ORANGEPLUS'], ['maimai ORANGE PLUS'], 1 << 4],
                 '桃': [['PiNK'], ['PiNK'], ['maimai PiNK'], 1 << 5],
                 '櫻': [['PiNKPLUS'], ['PiNKPLUS'], ['maimai PiNK PLUS'], 1 << 6],
                 '樱': [['PiNKPLUS'], ['PiNKPLUS'], ['maimai PiNK PLUS'], 1 << 6],
                 '紫': [['MURASAKi'], ['MURASAKi'], ['maimai MURASAKi'], 1 << 7],
                 '菫': [['MURASAKiPLUS'], ['MURASAKiPLUS'], ['maimai MURASAKi PLUS'], 1 << 8],
                 '堇': [['MURASAKiPLUS'], ['MURASAKiPLUS'], ['maimai MURASAKi PLUS'], 1 << 8],
                 '白': [['MiLK'], ['MiLK'], ['maimai MiLK'], 1 << 9],
                 '雪': [['MiLKPLUS'], ['MiLKPLUS'], ['MiLK PLUS'], 1 << 10],
                 '輝': [['FiNALE'], ['FiNALE'], ['maimai FiNALE'], 1 << 11],
                 '辉': [['FiNALE'], ['FiNALE'], ['maimai FiNALE'], 1 << 11],
                 '舞': [[], [], [], 1 << 12]}
for ver_ori in version_alias.values():
    version_alias['舞'][0] += ver_ori[0]
    version_alias['舞'][1] += ver_ori[1]
    version_alias['舞'][2] += ver_ori[2]
version_alias['舞'][0] = list(set(version_alias['舞'][0]))
version_alias['舞'][1] = list(set(version_alias['舞'][1]))
version_alias['舞'][2] = list(set(version_alias['舞'][2]))
version_alias.update({
    '熊': [['maimaDX'], ['舞萌DX'], ['maimai でらっくす'], 1 << 13],
    '華': [['maimaDXPLUS'], ['舞萌DX'], ['maimai でらっくす'], 1 << 13],
    '华': [['maimaDXPLUS'], ['舞萌DX'], ['maimai でらっくす'], 1 << 13],
    '爽': [['Splash'], ['舞萌DX 2021'], ['maimai でらっくす Splash'], 1 << 14],
    '煌': [['SplashPLUS'], ['舞萌DX 2022'], ['maimai でらっくす Splash PLUS'], 1 << 15]
})
ver_num_dict = {
    "真": 6100,
    "超": 6104,
    "檄": 6108,
    "橙": 6112,
    "暁": 6116,
    "桃": 6120,
    "櫻": 6124,
    "紫": 6128,
    "菫": 6132,
    "白": 6136,
    "雪": 6140,
    "輝": 6144,
    "覇者": 6148,
    "舞": 6149,
    "熊": 55101,
    "華": 109101,
    "爽": 159101
}
plate_ver_file = {
    '真': 'shin',
    '超': 'cho',
    '檄': 'geki',
    '橙': 'daidai',
    '暁': 'akatsuki',
    '晓': 'akatsuki',
    '桃': 'momo',
    '櫻': 'sakura',
    '樱': 'sakura',
    '紫': 'murasaki',
    '菫': 'sumire',
    '堇': 'sumire',
    '白': 'shira',
    '雪': 'yuki',
    '輝': 'akira',
    '辉': 'akira',
    '舞': 'mai',
    '熊': 'kuma-hana',
    '華': 'kuma-hana',
    '华': 'kuma-hana',
    '爽': 'sawa',
    '煌': 'kira'
}
plate_require = {
    "极": "FC",
    "極": "FC",
    "将": "SSS",
    "神": "AP",
    "舞舞": "FSD",
    "霸者": "A",
    "覇者": "A"
}
plate_num_dict = {
    "極": 0,
    "将": 1,
    "神": 2,
    "舞舞": 3
}

achie_ranks = {'SSS+': 100.5, 'SSS': 100, 'SS+': 99.5, 'SS': 99, 'S+': 98, 'S': 97, 'AAA': 94,
               'AA': 90, 'A': 80, 'BBB': 75, 'BB': 70, 'B': 60, 'C': 50, 'D': 0}
achie_ranks_regex = f"({'|'.join(achie_ranks.keys())})"
achie_ranks_regex = achie_ranks_regex.replace('+', '\+')
combo_ranks = {"AP+": 0, "app": 0, "ap": 1, "AP": 1, "FC+": 2, "fcp": 2, "fc": 3, "FC": 3, "": 4}
combo_ranks_regex = f"({'|'.join(combo_ranks.keys())})"
combo_ranks_regex = combo_ranks_regex.replace('+', '\+')
combo_upper = {"fc": "FC", "fcp": "FC+", "ap": "AP", "app": "AP+", "": ""}
sync_ranks = {"FSD+": 0, "fsdp": 0, "FSD": 1, "fsd": 1, "FS+": 2, "fsp": 2, "FS": 3, "fs": 3, "": 4}
sync_ranks_regex = f"({'|'.join(sync_ranks.keys())})"
sync_ranks_regex = sync_ranks_regex.replace('+', '\+')
sync_upper = {"fs": "FS", "fsp": "FS+", "fsd": "FSD", "fsdp": "FSD+", "fdx": "FSD", "fdxp": "FSD+", "": ""}

mai_dbpool = PooledDB(creator=pymysql, maxconnections=240, mincached=5, maxcached=None, blocking=True,
                      maxusage=None, ping=4, host="127.0.0.1", port=3306, user="anyone", password="UnpublicData",
                      database="maimai", charset="utf8")
player_dbpool = PooledDB(creator=pymysql, maxconnections=20, mincached=2, maxcached=None, blocking=True,
                         maxusage=None, ping=5, host="127.0.0.1", port=3306, user="anyone", password="UnpublicData",
                         database="Player", charset="utf8")
quotation_dbpool = PooledDB(creator=pymysql, maxconnections=10, mincached=3, maxcached=None, blocking=True,
                            maxusage=None, ping=4, host="127.0.0.1", port=3306, user="anyone",
                            password="UnpublicData", database="Quotations", charset="utf8")

mute_list = []
cpu_thread_amount = max(multiprocessing.cpu_count(), 4)


@lru_cache(400)
def fetch_song_cover(id: int):
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT Cover FROM SongInfo WHERE Id={id}")
    [img] = cursor.fetchone()
    conn.close()
    return img
