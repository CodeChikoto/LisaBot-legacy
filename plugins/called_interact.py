import re
import time
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from interact_func.select import *
from tools.image import *
from tools.shared_var import mute_list
from interact_func.emoji import *

bot_nick = ["lisa", "妈妈", "リサ"]
bot_nick_regex = f"^({'|'.join(bot_nick)})"
act = ["亲亲", "抱抱", "贴贴"]
random.seed(time.time())


async def _from_koto(bot: Bot, event: Event, state: dict) -> bool:
    return True if event.user_id == 993433577 else False


help_menu = on_regex(bot_nick_regex + " (help|帮助)", block=True)
select = on_regex(bot_nick_regex + " .+(or|还是|或者).+", block=True)
mute_mode = on_regex(bot_nick_regex + " (烟人|禁言)", block=True)
bully = on_regex(bot_nick_regex + " .+欺负我")
huge = on_regex(bot_nick_regex + f" ({'|'.join(act)})")
boom_leave = on_regex(bot_nick_regex + f" (退群|爆炸)", rule=_from_koto)


@help_menu.handle()
async def _(bot: Bot, event: Event, state: T_State):
    file_list = [open("text/help_maimai", "r"), open("text/help_interact", "r")]
    img_list = [image_to_base64(text_to_image(file.read())) for file in file_list]
    await help_menu.finish(Message([{
        "type": "image",
        "data": {
            "file": {f"base64://{str(img_list[0], encoding='utf-8')}"}
        }
    },
        {
        "type": "image",
        "data": {
            "file": f"base64://{str(img_list[1], encoding='utf-8')}"
        }
    }
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
        [emoji_id] = random.sample([1, 3], 1)
        msg = Message([
            {
                "type": "image",
                "data": {"file": f"{select_emoji(emoji_id)}"}
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
            "data": {"file": f"{random_emoji('joyful')}"}
        }
    ]))


@boom_leave.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        await bot.set_group_kick(group_id=event.group_id, user_id=993433577)
    finally:
        await bot.set_group_leave(group_id=event.group_id)
