from maimai_func.song_func import *
from maimai_func.chart_func import *
from maimai_func.best_list import *
from tools.image import *
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.typing import *
from tools.shared_var import *
from maimai_func.offline_func import *


async def _from_koto(bot: Bot, event: Event, state: dict) -> bool:
    return True if event.user_id == 993433577 else False


inner_level_search = on_regex("^定数查歌 " + difficulty_regex + "?([0-9]{1,2}\.[0-9])\s?([0-9]+)?", priority=2, block=True)
level_search = on_regex("^等级查歌 " + difficulty_regex + "?([0-9]+\+?)\s?([0-9]+)?", priority=2, block=True)
name_search = on_regex("^(search|查歌|搜索) (.+)$", priority=2, block=True)
artist_search = on_regex("^(曲师|艺术家|歌手)查歌 (.+)", priority=2, block=True)
view_song = on_regex("^id ([0-9]+)\s?(.+)?", priority=2, block=True)
view_chart = on_regex("^(看谱|查谱) " + difficulty_regex + "([0-9]+)\s?(.+)?", priority=2, block=True)
mai_what = on_regex(r".*mai\s?什么", priority=2, block=True)
which_is = on_regex("^(.+)是什么歌\s?([0-9]+)?$", priority=2, block=True)
achie_range = on_regex(f"^达成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                       r"([0-9]+),([0-9]+),([0-9]+),([0-9]+)", priority=2, block=True)
break_dist = on_regex(f"^绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                      f"([0-9]+),([0-9]+),([0-9]+),([0-9]+) ([0-9]+\.[0-9]+)", priority=2, block=True)
random_song = on_regex("^随歌" + difficulty_regex + "\s?([0-9]{1,2}\.[0-9])?([0-9]+\+?)?", priority=2, block=True)
try_random_chart = on_regex(r"^我要大战(.+)", priority=2, block=True)
best_list_pic = on_regex("^(b|B)(4|5)0\s?(.+)?", priority=2, block=True)
add_alias = on_regex("^增加别名 ([0-9]+) (.+)", priority=2, block=True)
show_alias = on_regex("^查看别名 ([0-9]+)", priority=2, block=True)
delete_alias = on_regex("^删除别名 ([0-9]+) (.+)", rule=_from_koto, priority=2, block=True)
achie_list = on_regex("^(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?")
level_process = on_regex("^进度 ([0-9]+\+?) " + achie_ranks_regex + "?\s?" + combo_ranks_regex + "?\s?"
                         + sync_ranks_regex + "?\s?(.+)?", priority=2, block=True)
plate_process = on_regex(f"^({'|'.join(version_alias.keys())})?({'|'.join(plate_require.keys())})进度\s?(.+)?"
                         , priority=2)
plate_list = on_regex("^牌子(条件|列表)\s?(.+)?", priority=2, block=True)
view_name_plate = on_command("view_plates_list", aliases={"查看名牌板", "查看姓名框"}, priority=2, block=True)
custom_name_plate = on_regex("^设置姓名框 ([0-9]+)", priority=2, block=True)
notes_search = on_regex("^物量查歌 ([0-9]+)\s?([0-9]+)?", priority=2, block=True)
bpm_search = on_regex("^(BPM|速度)查歌 ([0-9]+)\s?([0-9]+)?", priority=2, block=True)
rating_analyzation = on_regex("^(底分|Ra|Rating)分析", priority=2, block=True)
achi_line = on_regex("^(达成率|分数)线 " + difficulty_regex + "([0-9]+)\s?(0\+|100|101\-)?\s?(.+)?",
                     priority=2, block=True)
find_city_store = on_regex("^(查|寻)找机厅 (.+)", priority=2, block=True)
view_store = on_regex("^(机厅|店铺)信息 (.+)-([0-9]+)", priority=2, block=True)
rating_line = on_regex("^单曲(rating|ra) ([0-9]{1,2}\.[0-9])", priority=2, block=True)


@inner_level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_inner_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await inner_level_search.finish(final_msg)


@level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_level(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await level_search.finish(final_msg)


@name_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await name_search.finish(final_msg)


@artist_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_artist(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await artist_search.finish(final_msg)


@view_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = select_song_chart(str(event.get_message()))
    try:
        if img:
            await view_song.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "image",
                    "data": {"file": f"base64://{img}"}
                }
            ]))
        else:
            await view_song.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": text}
                }]))
    except CQHTTPAdapterException:
        await view_song.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "好像风控了，请稍后尝试并联系机修。"}
            }]))


@view_chart.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = select_chart(str(event.get_message()))
    try:
        await view_chart.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))
    except CQHTTPAdapterException:
        await view_chart.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))


@mai_what.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = random_by_aug("")
    if img:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            },
            {
                "type": "text",
                "data": {"text": text}
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
    await mai_what.send(final_msg)


@which_is.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await which_is.finish(final_msg)


@achie_range.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = cal_achie_range(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
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
                "data": {"file": f"base64://{img}"}
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


@random_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = random_by_aug(str(event.get_message()))
    try:
        await random_song.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))
    except CQHTTPAdapterException:
        await random_song.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))


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
    text, img = random_chart(str(event.get_message()))
    if text:
        try:
            await try_random_chart.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "image",
                    "data": {"file": f"base64://{img}"}
                },
                {
                    "type": "text",
                    "data": {"text": text}
                }]))
        except CQHTTPAdapterException:
            await try_random_chart.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": text}
                }]))
    else:
        await try_random_chart.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "有这位谱师嘛？"}
            }]))


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


@show_alias.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = show_alias_handle(str(event.get_message()))
    await show_alias.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@delete_alias.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = delete_alias_handle(str(event.get_message()))
    await delete_alias.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@achie_list.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await get_achie_list(str(event.get_message()), event.user_id)
    if img:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {
                    "file": f"base64://{img}"
                }
            }])
    elif text:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
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
    text = await get_plate_process(str(event.get_message()), event.user_id)
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ])
    await plate_process.finish(final_msg)


@plate_list.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = get_ver_plates(str(event.get_message()))
    if img:
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
    else:
        final_msg = Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }
        ])
    await plate_list.finish(final_msg)


@view_name_plate.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await view_name_plate.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "image",
            "data": {
                "file": f"file://{os.getcwd()}/material/plates/customizedable.png"
            }
        }]))


@custom_name_plate.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = set_name_plate(str(event.get_message()), event.user_id)
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ])
    await custom_name_plate.finish(final_msg)


@notes_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_notes_amount(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await notes_search.finish(final_msg)


@bpm_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = search_by_bpm(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await bpm_search.finish(final_msg)


@rating_analyzation.handle()
async def _(bot: Bot, event: Event, state: T_State):
    error, img = await analyze_rating(str(event.get_message()), event.user_id)
    if not error:
        await rating_analyzation.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            }
        ]))
    else:
        await rating_analyzation.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": error}
            }
        ]))


@achi_line.handle()
async def _(bot: Bot, event: Event, state: T_State):
    img, text = get_achi_line(str(event.get_message()))
    if text:
        await achi_line.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }
        ]))
    else:
        await achi_line.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            }
        ]))


@find_city_store.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = find_store(str(event.get_message()))
    if not img:
        await find_city_store.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))
    else:
        await find_city_store.finish(Message([
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
                "data": {"file": f"base64://{img}"}
            }
        ]))


@view_store.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = select_store(str(event.get_message()))
    await view_store.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }]))


@rating_line.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = cal_single_rating_line(str(event.get_message()))
    await rating_line.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }]))
