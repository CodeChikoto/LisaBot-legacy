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
    return True if event.user_id == 993433577 else False


async def _koto_muted(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "group_ban" and event.user_id == 993433577 and event.duration


async def _bot_muted(bot: Bot, event: Event, state: dict) -> bool:
    return event.notice_type == "group_ban" and event.user_id == int(bot.self_id) and event.duration


random.seed(time.time())
id, title, img_path = None, None, None

poke_back = on_notice(rule=_bot_poked, priority=2, block=True)
poke_mute = on_notice(rule=_mute_poke)
today_luck = on_command("today_luck", aliases={"今日运势"}, priority=2, block=True)
public_notice = on_command(rule=_from_koto, cmd="/public ", aliases={"/广播 ", "/公告 "}, block=True)
unmute_koto = on_notice(rule=_koto_muted)
remind_bot_muted = on_notice(rule=_bot_muted)


@poke_back.handle()
async def _(bot: Bot, event: Event, state: T_State):
    rand = random.randint(1, 12)
    # hit
    if 1 <= rand <= 4:
        await poke_back.finish(Message([
            {
                "type": "image",
                "data": {"file": f"base64://{await random_emoji('%')}"}
            }
        ]))
    # poke
    elif 5 <= rand <= 8:
        if event.__getattribute__('group_id') is None:
            event.__delattr__('group_id')
        await poke_back.finish(Message([
            {
                "type": "poke",
                "data": {"qq": f"{event.sender_id}"}
            }
        ]))
    elif 9 <= rand <= 10:
        await poke_back.finish(Message([
            {
                "type": "text",
                "data": {"text": mom()}
            }
        ]))
    else:
        await poke_back.finish()


@poke_mute.handle()
async def _(bot: Bot, event: Event, state: T_State):
    mute_time = random.randint(600, 2591999)
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=event.target_id, duration=mute_time)
    finally:
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
            "data": {"text": await cal_luck(event.get_user_id(), dict(event.sender)["nickname"])}
        }
    ])
    await today_luck.finish(msg)


@public_notice.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = event.get_message()
    groups_list = await bot.get_group_list()
    for group in groups_list:
        await bot.send_group_msg(group_id=group["group_id"],
                                 message=f"{time.strftime('%H:%M:%S')}给\"{group['group_name']}\"的推送消息：\n" + msg)
        time.sleep(random.randint(2, 5))


@unmute_koto.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        await bot.set_group_ban(group_id=event.group_id, user_id=993433577, duration=0)
    finally:
        await bot.send_private_msg(user_id=993433577, message=f"群{event.group_id}里你被{event.operator_id}禁言了！")


@remind_bot_muted.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await bot.send_private_msg(user_id=993433577, message=f"群{event.group_id}里我被{event.operator_id}禁言了！")
