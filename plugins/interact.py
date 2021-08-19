import random
import time
from nonebot import *
from nonebot.adapters import Event
from nonebot.adapters.cqhttp import *
from nonebot.typing import T_State
from interact_func.emoji import *

last_msg, repeated = None, False
random.seed(time.time())


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.target_id == int(bot.self_id))
    return value


poke_back = on_notice(rule=_group_poke, priority=10, block=True)


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


"""
async def _group_repeat(bot: Bot, event: Event, state: dict) -> bool:
    global last_msg, repeated
    if event.get_message() == last_msg:
        if not repeated:
            repeated = True
            return True
        else:
            return False
    else:
        last_msg = event.get_message()
        repeated = False
        return False


repeat = on_notice(rule=_group_repeat, priority=9, block=True)


@repeat.handle()
async def _(bot: Bot, event: Event, state: dict):
    msg = Message([
        {
            "type": "text",
            "data": {"text": str(event.get_message())}
        }
    ])
    await repeat.finish(msg)
"""
