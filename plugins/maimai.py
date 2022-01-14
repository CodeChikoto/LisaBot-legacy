from maimai_func.song_func import *
from maimai_func.chart_func import *
from maimai_func.best_list import *
from tools.image import *
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from tools.shared_var import *

inner_level_search = on_regex("定数查歌 " + difficulty_regex + "?([0-9]+\.[0-9])")
level_search = on_regex("等级查歌 " + difficulty_regex + "?([0-9]+\+?)")
name_search = on_command('name_search ', aliases={"查歌 ", "search "}, block=True)
artist_search = on_command("artist_search ", aliases={"艺术家查歌 ", "曲师查歌 "}, block=True)
view_song = on_regex("id ([0-9]+)\s?(.+)?", block=True)
view_chart = on_regex("(看谱|查谱) " + difficulty_regex + "([0-9]+)\s?(.+)?", block=True)
mai_what = on_regex(r".*mai\s?什么", block=True)
which_is = on_regex(r"(.+)是什么歌", block=True)
achie_range = on_regex(f"达成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+),([0-9]+)", block=True)
break_dist = on_regex(f"绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+),([0-9]+) ([0-9]+.[0-9]+)", block=True)
inner_level_random_song = on_regex("随歌 " + difficulty_regex + "\s?([0-9]+\.[0-9])")
level_random_song = on_regex("随歌 " + difficulty_regex + "\s?([0-9]+\+?)$")
try_random_chart = on_regex(r"我要大战(.+)", block=True)
best_list_pic = on_regex(r"^(b|B)(4|5)0\s?(.+)?")
add_alias = on_regex("增加别名 ([0-9]+) (.+)", block=True)
achie_list = on_regex(r"(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?")
level_process = on_regex("进度 ([0-9]+\+?) " + combo_ranks_regex + "\s?" + achie_ranks_regex + "\s?(.+)?")
plate_process = on_regex(f"^({'|'.join(version_alias.keys())})?({'|'.join(plate_alias.keys())})进度\s?(.+)?")
plate_list = on_command("plate_list", aliases={"牌子条件", "牌子列表"})


@inner_level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_inner_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await inner_level_search.finish(final_msg)


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
    msg, img_path = random_any()
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


@achie_range.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = cal_achie_range(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": msg}
        }])
    await achie_range.finish(final_msg)


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


@best_list_pic.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await best_list_pic.send(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": "ちょっと待ってください〜（B50 时间较长哦）"}
        }
    ]))
    img, error = await get_best_pic(str(event.get_message()), event.user_id)
    final_msg = None
    if error:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": error}
            }
        ])
    elif img:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            }
        ])
    await best_list_pic.finish(final_msg)


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
    add_alias_handle(str(event.get_message()))
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


@achie_list.handle()
async def _(bot: Bot, event: Event, state: T_State):
    data = await get_achie_list(str(event.get_message()), event.user_id)
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
    await achie_list.finish(final_msg)


@level_process.handle()
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
    await level_process.finish(final_msg)


@plate_process.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = await get_plate_process(str(event.get_message()), event.user_id)
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": msg}
        }
    ])
    await plate_process.finish(final_msg)


@plate_list.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await plate_list.finish(Message([
        {
            "type": "text",
            "data": {"text": "极 FC，将 SSS，神 AP，舞舞 FSD\n"}
        },
        {
            "type": "image",
            "data": {
                "file": f"file://{os.getcwd()}/material/PlateList.jpg"
            }
        }]))
