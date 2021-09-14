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
        else:
            return "", ""


# return: image path, text
def random_persecute(group_id: str):
    amount = cursor.execute(f"SELECT DISTINCT Aim FROM Group WHERE GroupId={group_id}")
    aim = cursor.fetchall()[random.randint(0, amount - 1)][0]
    amount = cursor.execute(f"SELECT No,Image,ImageExt FROM Group "
                            f"WHERE Aim='{aim}' AND GroupId={group_id}")
    res = cursor.fetchall()
    if not res:
        return "此群暂未开通迫害功能"
    image_data = res[random.randint(0, amount - 1)]
    cursor.execute(f"UPDATE Group SET Count=Count+1 WHERE No={image_data[0]}")
    with open("./temp" + image_data[2], "wb") as file:
        file.write(image_data[1])
    return f"file://{os.getcwd()}/cache" + image_data[2]


def add_persecution(group_id: str, aim: str):
    try:
        cursor.execute(f"INSERT INTO Group VALUES ({aim})")
    except Exception:
        return "此群未开通迫害功能"
