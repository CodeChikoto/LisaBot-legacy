import random
import time
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from interact_func.emoji import *
import re

random.seed(time.time())


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.target_id == int(bot.self_id))
    return value


poke_back = on_notice(rule=_group_poke, block=True)


@poke_back.handle()
async def _(bot: Bot, event: Event, state: T_State):
    rand = random.randint(1, 13)
    # hit
    if rand == 1:
        emoji_path = random_emoji("hit")
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"{emoji_path}"}
            }]
        ))
    elif rand == 2:
        emoji_path = random_emoji("shocked")
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"{emoji_path}"}
            }]
        ))
    # poke
    elif 3 <= rand <= 6:
        if event.__getattribute__('group_id') is None:
            event.__delattr__('group_id')
        await poke_back.finish(Message([
            {
                "type": "poke",
                "data": {"qq": f"{event.sender_id}"}
            }]
        ))
    elif 7 <= rand <= 8:
        await poke_back.finish(Message([
            {
                "type": "text",
                "data": {"text": mom("care")}
            }
        ]))
    else:
        await poke_back.finish()


# {group_id: last_message, count, has_repeated}
msg_record = {}

repeat = on_message()


@repeat.handle()
async def _(bot: Bot, event: Event, state: T_State):
    session_src = event.get_session_id().split('_')
    if session_src[0] == "group" and event.get_type() == "message":
        group_id, user_id = session_src[1], session_src[2]
        if group_id not in msg_record:
            msg_record[group_id] = [event.get_message(), 1]
        else:
            if event.get_message() == msg_record[group_id][0]:
                msg_record[group_id][1] += 1
                if msg_record[group_id][1] == 4:
                    await repeat.send(event.get_message())
            else:
                msg_record[group_id] = [event.get_message(), 1]
    await repeat.finish()


called = on_command("lisa ", aliases={"妈妈 ", "リサ ", "lisa "})


@called.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if str(event.get_message()) in ["随机迫害", "迫害个人"]:
        if re.match("group", event.get_session_id()) and \
                re.search("1025348679", event.get_session_id()):
            dir = os.listdir("emoji/persecute")
            person = random.sample(dir, 1)[0]
            dir = os.listdir("emoji/persecute/" + person)
            emoji = random.sample(dir, 1)[0]
            emoji_path = f"file://{os.getcwd()}/emoji/persecute/{person}/{emoji}"
            await poke_back.finish(Message([
                {
                    "type": "image",
                    "data": {"file": f"{emoji_path}"}
                }]
            ))
