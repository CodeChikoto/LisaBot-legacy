from maimai_func.song_func import *
from maimai_func.chart_func import *
from maimai_func.best_40 import generate
from tools.image import *
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *

with open("./text/difficulty_alias.json", "r") as file:
    difficulty_alias = json.load(file)
    chart_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")([0-9]+)"
    difficulty_regex = r"(" + r"|".join(difficulty_alias.keys()).lower() + r")"

base_search = on_command('inner_level_search ', aliases={'定数查歌 '}, block=True)
level_search = on_command('level_search ', aliases={'等级查歌 '}, block=True)
name_search = on_command('name_search ', aliases={"查歌 ", "search "}, block=True)
artist_search = on_command("artist_search ", aliases={"艺术家查歌 ", "曲师查歌 "}, block=True)
view_song = on_regex("id ([0-9]+)\s?(.+)?", block=True)
view_chart = on_command("view_chart ", aliases={"查谱 ", "看谱 "}, block=True)
mai_what = on_regex(r".*mai\s?什么", block=True)
which_is = on_regex(r".+是什么歌", block=True)
achiv_range = on_regex(f"完成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+),([0-9]+)", block=True)
break_dist = on_regex(f"绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+),([0-9]+) ([0-9]+.[0-9]+)", block=True)
inner_level_random_song = on_regex("随歌 " + difficulty_regex + "\s?([0-9]+\.[0-9])")
level_random_song = on_regex("随歌 " + difficulty_regex + "\s?([0-9]+\+?)$")
try_random_chart = on_regex(r"我要大战(.+)", block=True)
best_40_pic = on_command("best_40", aliases={"b40", "B40"}, block=True)
best_50_pic = on_command("best_50", aliases={"b50", "B50"}, block=True)
add_alias = on_command("增加别名", block=True)
achiv_list = on_regex(r"分数列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?")
level_rank_process = on_regex("进度 ([0-9]+\+?) " + combo_ranks_regex + "\s?" + score_ranks_regex + "\s?(.+)?")


@base_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_inner_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await base_search.finish(final_msg)


@level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await level_search.finish(final_msg)


@name_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await name_search.finish(final_msg)


@artist_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_artist(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await artist_search.finish(final_msg)


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
    try:
        await view_song.send(final_msg)
    except CQHTTPAdapterException:
        await view_song.send("ごめん〜风控了ね！\n" + msg)


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
    try:
        await view_chart.send(final_msg)
    except CQHTTPAdapterException:
        await view_chart.send("ごめん〜风控了ね！\n" + msg)


@mai_what.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_any("")
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
    await mai_what.send(final_msg)


@which_is.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await which_is.finish(final_msg)


@achiv_range.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = cal_achiv_range(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await achiv_range.finish(final_msg)


@break_dist.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = cal_break_dist(str(event.get_message()))
    if img:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{str(image_to_base64(img), encoding='utf-8')}"}
            }])
    else:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }])
    await break_dist.finish(final_msg)


@level_random_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_by_level(str(event.get_message()))
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
    try:
        await level_random_song.finish(final_msg)
    except CQHTTPAdapterException:
        await level_random_song.finish("ごめん〜风控了ね！\n" + msg)


@inner_level_random_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg, img_path = random_by_inner_level(str(event.get_message()))
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
    try:
        await inner_level_random_song.finish(final_msg)
    except CQHTTPAdapterException:
        await inner_level_random_song.finish("ごめん〜风控了ね！\n" + msg)


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
        try:
            await try_random_chart.finish(final_msg)
        except CQHTTPAdapterException:
            await try_random_chart.finish("ごめん〜风控了ね！\n" + msg)
    else:
        await try_random_chart.finish()


@add_alias.handle()
async def _(bot: Bot, event: Event, state: T_State):
    if add_alias_handle(str(event.get_message())):
        await add_alias.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "わかった！"}
            }
        ]))


@achiv_list.handle()
async def _(bot: Bot, event: Event, state: T_State):
    data = await get_achiv_list(str(event.get_message()), event.user_id)
    if isinstance(data, bytes):
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {
                    "file": f"base64://{str(data, encoding='utf-8')}"
                }
            }])
    elif isinstance(data, str):
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": data}
            }])
    await achiv_list.finish(final_msg)


@level_rank_process.handle()
async def _(bot: Bot, event: Event, state: T_State):
    data = await get_level_process(str(event.get_message()), event.user_id)
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": data}
        }
    ])
    await level_rank_process.finish(final_msg)
