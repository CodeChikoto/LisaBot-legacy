import random
import time
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from interact_func.emoji import *

random.seed(time.time())


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.target_id == int(bot.self_id))
    return value


poke_back = on_notice(rule=_group_poke, block=True)


@poke_back.handle()
async def _(bot: Bot, event: Event, state: T_State):
    rand = random.randint(1, 12)
    # hit
    if rand == 1:
        emoji_path = hit_person()
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"{emoji_path}"}
            }]
        ))
    # poke
    elif 2 <= rand <= 6:
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
            msg_record[group_id] = [event.get_message(), 1, False]
        else:
            if event.get_message() == msg_record[group_id][0]:
                msg_record[group_id][1] += 1
                if msg_record[group_id][1] > 3 and not msg_record[group_id][2]:
                    await repeat.send(event.get_message())
                    msg_record[group_id][2] = True
            else:
                msg_record[group_id] = [event.get_message(), 1, False]
    await repeat.finish()


