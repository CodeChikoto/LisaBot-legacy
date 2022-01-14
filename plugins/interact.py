import random
import time
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.adapters.cqhttp.bot import *
from nonebot.typing import *
from interact_func.cal_luck import *
from interact_func.emoji import *
from interact_func.selector import *
from plugins.called_interact import mute_list
import re


async def _bot_poked(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.target_id == int(bot.self_id))
    return value


async def _mute_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.user_id == 993433577 and event.target_id != 993433577 and
             event.group_id in mute_list)
    return value


async def _from_koto(bot: Bot, event: Event, state: dict) -> bool:
    value = event.message_type == "private" and event.user_id == 993433577
    return value


random.seed(time.time())
# {group_id: last_message, count, has_repeated}
msg_record = {}
in_song_guess = False
id, title, img_path, koto_last = None, None, None, None

poke_back = on_notice(rule=_bot_poked, block=True)
repeat = on_message()
is_online = on_regex(r"(.+)在线(么|吗)")
poke_mute = on_notice(rule=_mute_poke)
today_luck = on_command("today_luck", aliases={"今日运势"})
public_notice = on_command(rule=_from_koto, cmd="/public ", aliases={"/广播 ", "/公告 "})


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
            }
        ]))
    elif rand == 2:
        emoji_path = random_emoji("shocked")
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"{emoji_path}"}
            }
        ]))
    # poke
    elif 3 <= rand <= 6:
        if event.__getattribute__('group_id') is None:
            event.__delattr__('group_id')
        await poke_back.finish(Message([
            {
                "type": "poke",
                "data": {"qq": f"{event.sender_id}"}
            }
        ]))
    elif 7 <= rand <= 8:
        await poke_back.finish(Message([
            {
                "type": "text",
                "data": {"text": mom("care")}
            }
        ]))
    else:
        await poke_back.finish()


@repeat.handle()
async def _(bot: Bot, event: Event, state: T_State):
    global koto_last
    message, user_id = str(event.get_message()), event.user_id
    try:
        group_id = event.group_id
        if event.message_type == "group" and event.get_type() == "message":
            if group_id not in msg_record:
                msg_record[group_id] = [hash(message), 1]
            else:
                if hash(message) == msg_record[group_id][0]:
                    msg_record[group_id][1] += 1
                    if msg_record[group_id][1] == 4:
                        await repeat.send(message)
                else:
                    msg_record[group_id] = [hash(message), 1]
    except AttributeError:
        pass
    if user_id == 993433577:
        koto_last = time.time()
    await repeat.finish()


@is_online.handle()
async def _(bot: Bot, event: Event, state: T_State):
    global koto_last
    regex = r"(.+)在线(么|吗)"
    groups = re.match(regex, str(event.get_message())).groups()
    if groups[0] in ["琴琴", "琴"]:
        if not koto_last:
            await is_online.finish("重启后还没看到琴琴～")
        # in 30 minutes
        interval = time.time() - koto_last
        if not int(interval / 600):
            message = str(int(interval)) + "秒前に最後のメッセージ、いそうだ"
        elif not int(interval / 7200):
            # 30-60 minutes
            message = str(int(interval)) + "秒前に最後のメッセージ、いなさそうだ"
        else:
            message = "正体なく眠ています"
        await is_online.finish(message)


@poke_mute.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=event.target_id,
                                duration=864000)
    except CQHTTPAdapterException:
        pass
    await poke_mute.finish()


@today_luck.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": cal_luck(event.get_user_id(), dict(event.sender)["nickname"])}
        }
    ])
    await today_luck.finish(msg)


@public_notice.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = event.get_message()
    groups_list = await bot.get_group_list()
    for group in groups_list:
        await bot.send_group_msg(group_id=group["group_id"], message=msg)