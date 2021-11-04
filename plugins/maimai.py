from maimai_func.song_func import *
from interact_func.cal_luck import *
from interact_func.emoji import *
from maimai_func.chart_func import *
from maimai_func.best_40 import generate
from tools.image import *
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *

base_search = on_command('inner_level_search ', aliases={'定数查歌 '})


@base_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_inner_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await base_search.finish(final_msg)


level_search = on_command('level_search ', aliases={'等级查歌 '})


@level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await level_search.finish(final_msg)


name_search = on_command('name_search ', aliases={"查歌 ", "search "})


@name_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await name_search.finish(final_msg)


artist_search = on_command("artist_search ", aliases={"艺术家查歌 ", "曲师查歌 "})


@artist_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_artist(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await name_search.finish(final_msg)


view_song = on_command('view_song ', aliases={"id ", "ID "})


@view_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = select_song(str(event.get_message()))
    if img_path:
        final_msg = Message([
            {
                "type": "image",
                "data": {"file": f"{img_path}"}
            },
            {
                "type": "text",
                "data": {"text": msg}
            }])
    else:
        final_msg = Message([
            {
                "type": "text",
                "data": {"text": msg}
            }])
    await view_song.send(final_msg)


view_chart = on_command("view_chart ", aliases={"查谱 ", "看谱 "})


@view_chart.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = select_chart(str(event.get_message()))
    if img_path:
        final_msg = Message([
            {
                "type": "image",
                "data": {"file": f"{img_path}"}
            },
            {
                "type": "text",
                "data": {"text": msg}
            }])
    else:
        final_msg = Message([
            {
                "type": "text",
                "data": {"text": msg}
            }])
    await view_song.send(final_msg)


mai_what = on_regex(r".*mai.?什么")


@mai_what.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_song("")
    if img_path:
        final_msg = Message([
            {
                "type": "image",
                "data": {"file": f"{img_path}"}
            },
            {
                "type": "text",
                "data": {"text": msg}
            }])
    else:
        final_msg = Message([
            {
                "type": "text",
                "data": {"text": msg}
            }])
    await view_song.send(final_msg)


today_luck = on_command("today_luck", aliases={"今日运势", "今日舞萌"})


@today_luck.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = Message([
        {
            "type": "at",
            "data": {"qq": event.get_user_id()}
        },
        {
            "type": "text",
            "data": {"text": cal_luck(event.get_user_id())}
        }
    ])
    await today_luck.finish(msg)


which_is = on_regex(r".+是什么歌")


@which_is.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await name_search.finish(final_msg)


calculator = on_command("cal ", aliases={"计算器 ", "cal "})


@calculator.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = cal_ratio(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await calculator.finish(final_msg)


rule_random_song = on_command("rand_song ", aliases={"随歌"})


@rule_random_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_song(str(event.get_message()))
    if img_path:
        final_msg = Message([
            {
                "type": "image",
                "data": {"file": f"{img_path}"}
            },
            {
                "type": "text",
                "data": {"text": msg}
            }])
    else:
        final_msg = Message([
            {
                "type": "text",
                "data": {"text": msg}
            }])
    await rule_random_song.finish(final_msg)


best_40_pic = on_command("b40", aliases={"b40", "B40"})


@best_40_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    img, success = await generate(payload)
    if success == 400:
        await best_40_pic.send("未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。")
    elif success == 403:
        await best_40_pic.send("该用户禁止了其他人获取数据。")
    else:
        await best_40_pic.send(Message([
            {
                "type": "image",
                "data": {
                    "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
                }
            }
        ]))


best_50_pic = on_command("best_50", aliases={"b50", "B50"})


@best_50_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    username = str(event.get_message()).strip()
    if username == "":
        payload = {'qq': str(event.get_user_id())}
    else:
        payload = {'username': username}
    payload["b50"] = True
    img, success = await generate(payload)
    if success == 400:
        await best_50_pic.send("未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。")
    elif success == 403:
        await best_50_pic.send("该用户禁止了其他人获取数据。")
    else:
        await best_50_pic.send(Message([
            {
                "type": "image",
                "data": {
                    "file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"
                }
            }
        ]))


try_random_chart = on_regex(r"(我要大战)(.+)(!｜。|)")


@try_random_chart.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_chart(str(event.get_message()))
    if msg:
        if img_path:
            final_msg = Message([
                {
                    "type": "image",
                    "data": {"file": f"{img_path}"}
                },
                {
                    "type": "text",
                    "data": {"text": msg}
                }])
        else:
            final_msg = Message([
                {
                    "type": "text",
                    "data": {"text": msg}
                }])
        await try_random_chart.finish(final_msg)
    else:
        await try_random_chart.finish()
