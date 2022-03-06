from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from interact_func.cal_luck import *
from interact_func.emoji import *
from interact_func.select import *
from tools.shared_var import *


async def _bot_poked(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "notify" and event.sub_type == "poke" and event.target_id == int(bot.self_id)


async def _mute_poke(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "notify" and event.sub_type == "poke" and event.user_id == 993433577 and \
           event.target_id != 993433577 and event.group_id in mute_list


async def _from_koto(bot: Bot, event: Event, state: dict) -> bool:
    global koto_last
    if event.user_id == 993433577:
        koto_last = time.strftime("%d.%H:%M:%S")
        return True
    return False


async def _koto_muted(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "group_ban" and event.user_id == 993433577 and event.duration


async def _bot_muted(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "group_ban" and event.user_id == int(bot.self_id) and event.duration



random.seed(time.time())
# {group_id: last_message, count}
msg_record = {}
id, title, img_path, koto_last = None, None, None, None

poke_back = on_notice(rule=_bot_poked, priority=2, block=True)
repeat = on_message(priority=3)
is_online = on_regex(r"^(琴|琴琴|机修)在线(么|吗)(？|)", priority=2, block=True)
poke_mute = on_notice(rule=_mute_poke)
today_luck = on_command("today_luck", aliases={"今日运势"}, priority=2, block=True)
public_notice = on_command(rule=_from_koto, cmd="/public ", aliases={"/广播 ", "/公告 "}, block=True)
unmute_koto = on_notice(rule=_koto_muted)
remind_bot_muted = on_notice(rule=_bot_muted)


@poke_back.handle()
async def _(bot: Bot, event: Event, state: T_State):
    rand = random.randint(1, 12)
    # hit
    if 1 <= rand <= 3:
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"{random_emoji('%')}"}
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
    await repeat.finish()


@is_online.handle()
async def _(bot: Bot, event: Event, state: T_State):
    global koto_last
    if koto_last:
        text = f"{koto_last}に最後のメッセージ"
        now = time.strftime("%d.%H:%M:%S")
        last, now = re.split("\.|:", koto_last), re.split("\.|:", now)
        # in 30 minutes
        if last[0] == now[0] and last[1] == now[1] and int(now[2]) - int(last[2]) <= 30:
            text += "\n絶対にいますね！"
        # 30 minutes ~ 1 hour
        elif last[0] == now[0] and last[1] == now[1] and int(now[2]) - int(last[2]) <= 60:
            text += "\nいそうです！"
        # 1 hour ~ 3 hour
        elif last[0] == now[0] and int(now[1]) - int(last[1]) <= 3:
            text += "\nいなさそうです！"
        else:
            text += "\n正体なく眠ています"
    else:
        text = "重启后还没见过琴琴"
    await is_online.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "at",
            "data": {"qq": "993433577"}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@poke_mute.handle()
async def _(bot: Bot, event: Event, state: T_State):
    mute_time = random.randint(600, 2591999)
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=event.target_id, duration=mute_time)
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
        time.sleep(2)


@unmute_koto.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=993433577, duration=0)
    finally:
        await bot.send_private_msg(user_id=993433577, message=f"群{event.group_id}里你被{event.operator_id}禁言了！")


@remind_bot_muted.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await bot.send_private_msg(user_id=993433577, message=f"群{event.group_id}里我被{event.operator_id}禁言了！")
