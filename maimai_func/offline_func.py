import re
from tools.shared_var import *
from tools.image import *


async def find_store(user_in: str):
    regex = "^(查|寻)?找机厅 (.+)"
    _, place = re.match(regex, user_in).groups()
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id,Name FROM Store WHERE City='{place}' "
                   f"UNION SELECT id,Name FROM Store WHERE Province='{place}'")
    ans = cursor.fetchall()
    if not ans:
        return f"没有在{place}找到舞萌DX呢～", ""
    else:
        return f"在{place}找到了{len(ans)}家店铺：\n", \
               str(image_to_base64(text_to_image("\n".join(["  ".join(a) for a in ans]))), encoding="utf-8")


async def select_store(user_in: str):
    regex = "^(机厅|店铺)信息 (.+)-([0-9]+)"
    _, city, id = re.match(regex, user_in).groups()
    conn = mai_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT id,Name,Address,CoinPrice,CoinPerPlay,MachineAmount,MidPrice,Note,StartTime,CloseTime "
                   f"FROM Store WHERE id='{city}-{id}'")
    ans = cursor.fetchone()
    if not ans:
        return "真的有这家机厅么？"
    else:
        text = f"店铺编号：{ans[0]}\n" \
               f"店铺名称：{ans[1]}\n" \
               f"详细地址：{ans[2]}\n"
        text += f"营业时间：{ans[8]}-{ans[9]}\n" \
                f"单币价格：{str(ans[3]).rstrip('0').rstrip('.')}\n" \
                f"机台币数：{ans[4]}\n" \
                f"机台数量：{ans[5]}\n" \
                f"单局价格中位数：{str(ans[6]).rstrip('0').rstrip('.')}\n" \
                f"备注：{ans[7]}" if any(ans[3:]) else \
            "这个店铺的信息需要完善，可前往 https://wj.qq.com/s2/9847746/6fe2/ 提交数据。"
    return text
