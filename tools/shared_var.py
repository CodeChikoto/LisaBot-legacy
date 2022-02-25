import pymysql
from dbutils.pooled_db import PooledDB


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
    "": ""}
difficulty_short = ["BSC", "ADV", "EXP", "MST", "REM"]
chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")([0-9]+)"
difficulty_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")"

# [0] match Koto's database (JapanVer), [1] match Koto's database (ChinaVer), [2] match diving-fish databse
version_aliases = {'真': [['maimai', 'maimai PLUS'], ['maimai', 'maimai PLUS'], ['maimai', 'maimai PLUS']],
                   '超': [['maimai GreeN'], ['maimai GreeN'], ['maimai GreeN']],
                   '檄': [['maimai GreeN PLUS'], ['maimai GreeN PLUS'], ['maimai GreeN PLUS']],
                   '橙': [['maimai ORANGE'], ['maimai ORANGE'], ['maimai ORANGE']],
                   '暁': [['maimai ORANGE PLUS'], ['maimai ORANGE PLUS'], ['maimai ORANGE PLUS']],
                   '晓': [['maimai ORANGE PLUS'], ['maimai ORANGE PLUS'], ['maimai ORANGE PLUS']],
                   '桃': [['maimai PiNK'], ['maimai PiNK'], ['maimai PiNK']],
                   '櫻': [['maimai PiNK PLUS'], ['maimai PiNK PLUS'], ['maimai PiNK PLUS']],
                   '樱': [['maimai PiNK PLUS'], ['maimai PiNK PLUS'], ['maimai PiNK PLUS']],
                   '紫': [['maimai MURASAKi'], ['maimai MURASAKi'], ['maimai MURASAKi']],
                   '菫': [['maimai MURASAKi PLUS'], ['maimai MURASAKi PLUS'], ['maimai MURASAKi PLUS']],
                   '堇': [['maimai MURASAKi PLUS'], ['maimai MURASAKi PLUS'], ['maimai MURASAKi PLUS']],
                   '白': [['maimai MiLK'], ['maimai MiLK'], ['maimai MiLK']],
                   '雪': [['maimai MiLK PLUS'], ['maimai MiLK PLUS'], ['MiLK PLUS']],
                   '輝': [['maimai FiNALE'], ['maimai FiNALE'], ['maimai FiNALE']],
                   '辉': [['maimai FiNALE'], ['maimai FiNALE'], ['maimai FiNALE']], '舞': [[], [], []]}
for ver_ori in version_aliases.values():
    version_aliases['舞'][0] += ver_ori[0]
    version_aliases['舞'][1] += ver_ori[1]
    version_aliases['舞'][2] += ver_ori[2]
version_aliases['舞'][0] = list(set(version_aliases['舞'][0]))
version_aliases['舞'][1] = list(set(version_aliases['舞'][1]))
version_aliases['舞'][2] = list(set(version_aliases['舞'][2]))
version_aliases.update({
    '熊': [['maimai DX'], ['舞萌DX'], ['maimai でらっくす']],
    '華': [['maimai DX PLUS'], ['舞萌DX'], ['maimai でらっくす']],
    '华': [['maimai DX PLUS'], ['舞萌DX'], ['maimai でらっくす']],
    '爽': [['maimai DX Splash'], ['舞萌DX 2021'], ['maimai でらっくす Splash']],
    '煌': [['maimai DX Splash PLUS'], ['舞萌DX 2021'], ['maimai でらっくす Splash PLUS']]
})
ver_num_list = {
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

plate_require = {
    "极": "FC",
    "極": "FC",
    "将": "SSS",
    "神": "AP",
    "舞舞": "FSD",
    "霸者": "A",
    "覇者": "A"
}
plate_num_list = {
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
sync_ranks = {"FSD+": 0, "FSD": 1, "FS+": 2, "FS": 3, "": 4}
sync_ranks_regex = f"({'|'.join(sync_ranks.keys())})"
sync_ranks_regex = sync_ranks_regex.replace('+', '\+')
sync_upper = {"fs": "FS", "fsp": "FS+", "fsd": "FSD", "fsdp": "FSD+", "fdx": "FSD", "fdxp": "FSD+", "": ""}

new_id_list = [10021, 10181, 10188, 10690, 11032, 11089, 11090, 11091, 11092, 11097, 11098, 11099, 11100, 11101,
               11102, 11103, 11105, 11107, 11108, 11109, 11110, 11111, 11113, 11114, 11115, 11125, 11126, 11127,
               11128, 11129, 11130, 11131, 11132, 11133, 11135, 11136, 11137, 11138, 11139, 11141, 11142, 11143,
               11146, 11147, 11148, 11149, 11150, 11152, 11153, 11154, 11155, 11157, 11158, 11159, 11160, 11161,
               11162, 11163, 11164, 11168, 11171, 11175, 11176, 11177, 11178, 11179, 11180, 11184, 11185, 11186,
               11187, 11188, 11189, 11190, 11191, 11192, 11193, 11194, 11195, 11198, 11199, 11200, 11206, 11210,
               11211, 11212, 11213, 11214, 11215, 11216, 11217, 11221]
mai_dbpool = PooledDB(creator=pymysql, maxconnections=480, mincached=5, maxcached=None, blocking=True,
                      maxusage=None, ping=4, host="39.106.184.73", port=3306, user="anyone", password="UnpublicData",
                      database="maimai", charset="utf8")
player_dbpool = PooledDB(creator=pymysql, maxconnections=10, mincached=5, maxcached=None, blocking=True,
                      maxusage=None, ping=4, host="39.106.184.73", port=3306, user="anyone", password="UnpublicData",
                      database="Player", charset="utf8")
quotation_dbpool = PooledDB(creator=pymysql, maxconnections=10, mincached=5, maxcached=None, blocking=True,
                      maxusage=None, ping=4, host="39.106.184.73", port=3306, user="anyone", password="UnpublicData",
                      database="Quotations", charset="utf8")
mute_list = []
