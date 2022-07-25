from functools import lru_cache
import multiprocessing
from models.mai_models import *

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
                 '桃': [['PiNK'], ['PiNK'], ['maimai PiNK'], 1 << 5],
                 '櫻': [['PiNKPLUS'], ['PiNKPLUS'], ['maimai PiNK PLUS'], 1 << 6],
                 '紫': [['MURASAKi'], ['MURASAKi'], ['maimai MURASAKi'], 1 << 7],
                 '菫': [['MURASAKiPLUS'], ['MURASAKiPLUS'], ['maimai MURASAKi PLUS'], 1 << 8],
                 '白': [['MiLK'], ['MiLK'], ['maimai MiLK'], 1 << 9],
                 '雪': [['MiLKPLUS'], ['MiLKPLUS'], ['MiLK PLUS'], 1 << 10],
                 '輝': [['FiNALE'], ['FiNALE'], ['maimai FiNALE'], 1 << 11],
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
    '爽': [['Splash'], ['舞萌DX2021'], ['maimai でらっくす Splash'], 1 << 14],
    '煌': [['SplashPLUS'], ['舞萌DX2021'], ['maimai でらっくす Splash'], 1 << 14]
})
all_versions = []
for alias in version_alias.keys():
    all_versions += version_alias[alias][2]
all_versions = list(set(all_versions))
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
    '桃': 'momo',
    '櫻': 'sakura',
    '紫': 'murasaki',
    '菫': 'sumire',
    '白': 'shira',
    '雪': 'yuki',
    '輝': 'akira',
    '舞': 'mai',
    '熊': 'kuma-hana',
    '華': 'kuma-hana',
    '爽': '2021',
    '煌': '2021',
    '宙': 'uni'
}
plate_require = {
    "極": "FC",
    "将": "SSS",
    "神": "AP",
    "舞舞": "FSD",
    "覇者": "A"
}
plate_num_dict = {
    "極": 0,
    "将": 1,
    "神": 2,
    "舞舞": 3
}

achievements_ranks = {'SSS+': 100.5, 'SSSp': 100.5, 'SSS': 100, 'SS+': 99.5, 'SSp': 99.5, 'SS': 99, 'S+': 98, 'Sp': 98,
               'S': 97, 'AAA': 94, 'AA': 90, 'A': 80, 'BBB': 75, 'BB': 70, 'B': 60, 'C': 50, 'D': 0}
achievements_ranks_regex = f"({'|'.join(achievements_ranks.keys())})"
achievements_ranks_regex = achievements_ranks_regex.replace('+', '\+')
combo_ranks = {"AP+": 0, "APp": 0, "app": 0, "ap": 1, "AP": 1,
               "FC+": 2, "FCp": 2, "fcp": 2, "fc": 3, "FC": 3,
               "": 4}
combo_ranks_regex = f"({'|'.join(combo_ranks.keys())})"
combo_ranks_regex = combo_ranks_regex.replace('+', '\+')
combo_upper = {"fc": "FC", "fcp": "FC+", "ap": "AP", "app": "AP+", "": ""}
sync_ranks = {"FSD+": 0, "fsdp": 0, "FSDp": 0, "FSD": 1, "fsd": 1,
              "FS+": 2, "fsp": 2, "FSp": 2, "FS": 3, "fs": 3,
              "": 4}
sync_ranks_regex = f"({'|'.join(sync_ranks.keys())})"
sync_ranks_regex = sync_ranks_regex.replace('+', '\+')
sync_upper = {"fs": "FS", "fsp": "FS+", "fsd": "FSD", "fsdp": "FSD+", "fdx": "FSD", "fdxp": "FSD+", "": ""}

superuser = (993433577, 1826356872, 1873618331, 583718334)

mute_list = []
cpu_thread_amount = multiprocessing.cpu_count()


@lru_cache(400)
def fetch_song_cover(id: int):
    song = SongInfo.get_or_none(SongInfo.id == id)
    return song.cover
