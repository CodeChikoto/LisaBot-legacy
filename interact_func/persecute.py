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
        if arg in ["随机迫害", "迫害", "来点圣经"]:
            return random_persecute(group_id)
        else:
            return "", ""
            """
            args = arg.split()
            if args[0] in ["新增迫害", "增加迫害"] and args[1]:
            """


# return: image path, text
def random_persecute(group_id: str):
    try:
        amount = cursor.execute(f"SELECT DISTINCT Aim FROM Group{group_id}")
        aim = cursor.fetchall()[random.randint(0, amount - 1)][0]
        amount = cursor.execute(f"SELECT Screenshot FROM Group{group_id} "
                                f"WHERE Aim='{aim}'")
        rand_int = random.randint(0, amount - 1)
        image = cursor.fetchall()[rand_int][0]
        # cursor.execute(f"UPDATE Group{group_id} SET Count=Count+1 WHERE Aim='{aim}' "
        #                f"LIMIT {rand_int},1")
        with open("./cache.jpg", "wb") as file:
            file.write(image)
        return f"file://{os.getcwd()}/cache.jpg"
    except Exception:
        return "此群未开通迫害功能"


def add_persecution(group_id: str, aim: str):
    try:
        cursor.execute(f"INSERT INTO Group{group_id} VALUES ({aim})")
    except Exception:
        return "此群未开通迫害功能"