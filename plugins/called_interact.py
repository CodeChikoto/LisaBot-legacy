from _thread import start_new_thread
from sched import scheduler
import nonebot.matcher
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from interact_func.select import *
from tools.image import *
from interact_func.emoji import *
from pyrate_limiter import (BucketFullException, Duration, RequestRate, Limiter, MemoryListBucket)


def _update_blacklist():
    global blacklist
    conn = player_dbpool.connection()
    cursor = conn.cursor()
    cursor.execute("SELECT QQId FROM Blacklist")
    blacklist = [int(ans[0]) for ans in cursor.fetchall()]
    blacklist_updater.enter(8640, 0, _update_blacklist, ())


bot_nick = ["lisa", "妈妈", "リサ"]
bot_nick_regex = f"^({'|'.join(bot_nick)})"
act = ["亲亲", "抱抱", "贴贴"]
random.seed(time.time())
blacklist = []
blacklist_updater = scheduler(time.time, time.sleep)
blacklist_updater.enter(0, 0, _update_blacklist, ())
start_new_thread(blacklist_updater.run, ())
minute_rate = RequestRate(12, Duration.MINUTE)
limiter = Limiter(minute_rate, bucket_class=MemoryListBucket)


async def _from_koto(bot: Bot, event: Event, state: dict) -> bool:
    return event.user_id == 993433577


async def _in_blacklist(bot: Bot, event: Event, state: dict) -> bool:
    value = event.user_id in blacklist
    try:
        limiter.try_acquire(event.group_id if event.message_type == "group" else event.user_id)
    except BucketFullException:
        value = True
    return value


help_menu = on_regex(bot_nick_regex + " (help|帮助)", priority=2, block=True)
select = on_regex(bot_nick_regex + " .+(or|还是|或者).+", priority=2, block=True)
mute_mode = on_regex(bot_nick_regex + " (烟人|禁言)", block=True)
bully = on_regex(bot_nick_regex + " .+欺负我", priority=2)
huge = on_regex(bot_nick_regex + f" ({'|'.join(act)})", priority=2)
boom_leave = on_regex(bot_nick_regex + f" (退群|爆炸)", rule=_from_koto)
manage_blacklist = on_regex(bot_nick_regex + f" (移除|移出|添加|增加|加入)黑名单 ([0-9]+)")
ignore = on_message(rule=_in_blacklist, priority=1, block=True)
set_message_rate = on_regex(bot_nick_regex + f" 发言速率 ([0-9]+)", rule=_from_koto)


@help_menu.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await help_menu.finish(Message([{
        "type": "image",
        "data": {
            "file": f"base64://{str(image_to_base64(text_to_image(open('text/help', 'r').read())), encoding='utf-8')}"
        }
    },
    ]))


@select.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await select.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": auto_select(str(event.get_message()))}
        }
    ]))


@mute_mode.handle()
async def _(bot: Bot, event: Event, state: T_State):
    user_id = event.user_id
    if user_id == 993433577:
        _, _, state = re.match(bot_nick_regex + " (烟人|禁言)" + " (.+)", str(event.get_message())).groups()
        if state in ["1", "on", "始まって"] and event.group_id not in mute_list:
            mute_list.append(event.group_id)
            await mute_mode.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": "はい〜"}
                }
            ]))
        elif state in ["0", "off", "終わって"] and event.group_id in mute_list:
            mute_list.remove(event.group_id)
            await mute_mode.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": "はい〜"}
                }
            ]))


@bully.handle()
async def _(bot: Bot, event: Event, state: T_State):
    [_, aim] = re.match(bot_nick_regex + " (.+)欺负我", str(event.get_message())).groups()
    if aim.lower() in ["琴琴", "琴", "琴琴琴", "妈妈", "リサ", "夏洛缇", "宜酱", "三琴", "钾哥", "lisa", "charlotte"]:
        msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": aim + "是绝对不会欺负你的！"}
            }
        ])
    else:
        emoji_id = random.choice([1, 3])
        msg = Message([
            {
                "type": "image",
                "data": {"file": f"base64://{select_emoji(emoji_id)}"}
            },
            {
                "type": "text",
                "data": {"text": f"@{aim}"}
            }
        ])
    await bully.finish(msg)


@huge.handle()
async def _(bot: Bot, event: Event, state: T_State):
    _, text = re.match(bot_nick_regex + f" ({'|'.join(act)})", str(event.get_message())).groups()
    await huge.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text + "\n"}
        },
        {
            "type": "image",
            "data": {"file": f"base64://{random_emoji('joyful')}"}
        }
    ]))


@boom_leave.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        await bot.set_group_kick(group_id=event.group_id, user_id=993433577)
    finally:
        await bot.set_group_leave(group_id=event.group_id)


@manage_blacklist.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if event.user_id not in [993433577]:
        await manage_blacklist.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "ごめん？？？？"}
            }
        ]))
    regex = bot_nick_regex + f" (移除|移出|添加|增加|加入)黑名单 ([0-9]+)"
    _, op, aim_id = re.match(regex, str(event.get_message())).groups()
    aim_id = int(aim_id)
    conn = player_dbpool.connection()
    cursor = conn.cursor()
    if op in ["移除", "移出"]:
        cursor.execute(f"DELETE FROM Blacklist WHERE QQId={aim_id}")
        if aim_id in blacklist:
            blacklist.remove(aim_id)
    else:
        cursor.execute(f"INSERT IGNORE Blacklist VALUES ({aim_id})")
        if aim_id not in blacklist:
            blacklist.append(aim_id)
    conn.commit()
    await manage_blacklist.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": "はい！"}
        }
    ]))


@ignore.handle()
async def _(bot: Bot, event: Event, state: T_State, matcher: nonebot.matcher.Matcher):
    matcher.stop_propagation()
    await ignore.finish()


@set_message_rate.handle()
async def _(bot: Bot, event: Event, state: T_State):
    global minute_rate, limiter
    regex = bot_nick_regex + f" 发言速率 ([0-9]+)"
    _, rate = re.match(regex, str(event.get_message())).groups()
    minute_rate = RequestRate(int(rate), Duration.MINUTE)
    limiter = Limiter(minute_rate, bucket_class=MemoryListBucket)