import re
import os
import random
from tools.database import *
import time

random.seed(time.time())
cursor = Cursor(database="Quotations")


def persecute(arg: str, session: str):
    arg = arg.strip()
    if re.match("group", session):
        group_id = session.split('_')[1]
        if arg in ["随机迫害", "迫害"]:
            return random_persecute(group_id)
        elif arg in ["迫害出货率", "迫害概率"]:
            return cal_rarity(group_id)


# return: image path, text
def random_persecute(group_id: str):
    amount = cursor.execute(f"SELECT DISTINCT Aim FROM `Group` WHERE GroupId='{group_id}'")
    aim = cursor.fetchall()[random.randint(0, amount - 1)][0]
    amount = cursor.execute(f"SELECT No,Image,ImageExt FROM `Group` "
                            f"WHERE Aim='{aim}' AND GroupId='{group_id}'")
    res = cursor.fetchall()
    if not res:
        return "此群暂未开通迫害功能"
    image_data = res[random.randint(0, amount - 1)]
    cursor.execute(f"UPDATE `Group` SET Count=Count+1 WHERE No='{image_data[0]}'")
    cursor.commit()
    with open("./temp" + image_data[2], "wb") as file:
        file.write(image_data[1])
    return f"file://{os.getcwd()}/temp" + image_data[2]


def add_persecution(group_id: str, aim: str):
    try:
        cursor.execute(f"SELECT MAX(No) FROM `Group` WHERE Aim='{aim}'")
        no = int(cursor.fetchone()[0]) + 1
        cursor.execute(f"INSERT INTO `Group` (No,Aim,GroupId,Image,ImageExt,Count) "
                       f"VALUES ('{str(no)}','{aim}','{group_id}',)")
    except Exception:
        return "此群未开通迫害功能"


def cal_rarity(group_id: str):
    rarity = ["CC", "C", "R", "SR", "SSR"]
    amount = cursor.execute("SELECT Aim,SUM(Count) FROM `Group` GROUP BY GroupId,Aim "
                            "ORDER BY SUM(Count) DESC")
    if not amount:
        return "此群未有迫害图鉴"
    # res: [[aim, count]]
    res = cursor.fetchall()
    msg = "卡池出货率："
    for i in range(amount):
        msg += f"\n{rarity[int(i * 5 / amount)]} {res[i][0]}"
    return msg
