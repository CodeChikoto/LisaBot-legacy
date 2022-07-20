from maimai_func.song_func import *
from maimai_func.chart_func import *
from maimai_func.user_data_func import *
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
song_charts_viewing = on_regex("^id ([0-9]+)\s?(.+)?", priority=2, block=True)
song_viewing = on_regex("^ma?i?song ([0-9]+)\s?(.+)?", priority=2, block=True)
chart_viewing = on_regex("^ma?i?chart " + difficulty_regex + "([0-9]+)\s?(.+)?", priority=2, block=True)
another_song_random = on_regex(r".*mai\s?什么", priority=2, block=True)
another_name_search = on_regex("^(.+)是什么歌\s?([0-9]+)?$", priority=2, block=True)
achievements_range = on_regex(f"^达成率范围 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                              r"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                              r"([0-9]+),([0-9]+),([0-9]+),([0-9]+)", priority=2, block=True)
break_dist_calculation = on_regex(f"^绝赞分布 {chart_regex} ([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                                  f"([0-9]+),([0-9]+),([0-9]+) ([0-9]+),([0-9]+),([0-9]+) "
                                  f"([0-9]+),([0-9]+),([0-9]+),([0-9]+) ([0-9]+\.[0-9]+)", priority=2, block=True)
song_random = on_regex("^随歌" + difficulty_regex + "\s?([0-9]{1,2}\.[0-9])?([0-9]+\+?)?", priority=2, block=True)
chart_random = on_regex(r"^我要大战(.+)", priority=2, block=True)
best_list_query = on_regex("^(b|B)(4|5)0\s?(.+)?", priority=2, block=True)
alias_addition = on_regex("^增加别名 ([0-9]+) (.+)", priority=2, block=True)
alias_showing = on_regex("^查看别名 ([0-9]+)", priority=2, block=True)
alias_deletion = on_regex("^删除别名 ([0-9]+) (.+)", rule=_from_koto, priority=2, block=True)
level_list_showing = on_regex("^(分数|达成率)列表 ([0-9]+\+?)\s?([0-9]+)?\s?(.+)?")
level_process_showing = on_regex("^进度 ([0-9]+\+?) " + combo_ranks_regex + "?\s?" + sync_ranks_regex + "?\s?"
                                 + achie_ranks_regex + "?\s?(.+)?", priority=2, block=True)
plate_process_showing = on_regex(f"^(.+)进度\s?(.+)?", priority=2, block=True)
plate_requirements_showing = on_regex("^牌子(条件|列表)\s?(.+)?", priority=2, block=True)
name_plates_viewing = on_command("name_plates_viewing", aliases={"查看名牌板", "查看姓名框"}, priority=2, block=True)
name_plate_configuration = on_regex("^设置姓名框 ([0-9]+)", priority=2, block=True)
notes_search = on_regex("^物量查歌 ([0-9]+)\s?([0-9]+)?", priority=2, block=True)
bpm_search = on_regex("^(bpm|BPM|速度)查歌 ([0-9]+)\s?([0-9]+)?", priority=2, block=True)
rating_analysis = on_regex("^(底分|Ra|Rating|ra|rating)分析", priority=2, block=True)
achievements_line_calculation = on_regex("^(达成率|分数)线 " + difficulty_regex + "([0-9]+)\s?(0\+|100|101\-)?\s?(.+)?",
                                         priority=2, block=True)
stores_finding = on_regex("^(查|寻)找机厅 (.+)", priority=2, block=True)
store_viewing = on_regex("^(机厅|店铺)信息 (.+)-([0-9]+)", priority=2, block=True)
rating_line_showing = on_regex("^单曲(rating|ra|Ra|Rating) ([0-9]{1,2}\.[0-9])", priority=2, block=True)


@inner_level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await search_by_inner_level(str(event.get_message()))
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
    text = await search_by_level(str(event.get_message()))
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
    text = await search_by_name(str(event.get_message()))
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
    text = await search_by_artist(str(event.get_message()))
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


@song_viewing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await select_song(str(event.get_message()))
    try:
        if img:
            await song_charts_viewing.send(Message([
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
                }
            ]))
    except CQHTTPAdapterException:
        await song_charts_viewing.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "好像风控了，请稍后尝试并联系机修。"}
            }
        ]))


@song_charts_viewing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await select_song_charts(str(event.get_message()))
    try:
        if img:
            await song_charts_viewing.send(Message([
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
            await song_charts_viewing.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": text}
                }]))
    except CQHTTPAdapterException:
        await song_charts_viewing.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "好像风控了，请稍后尝试并联系机修。"}
            }]))


@chart_viewing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await select_chart(str(event.get_message()))
    try:
        await chart_viewing.send(Message([
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
        await chart_viewing.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))


@another_song_random.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await random_by_aug("随歌")
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
    await another_song_random.send(final_msg)


@another_name_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await search_by_name(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await another_name_search.finish(final_msg)


@achievements_range.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await cal_achievements_range(str(event.get_message()))
    final_msg = Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }])
    await achievements_range.finish(final_msg)


@break_dist_calculation.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await cal_break_dist(str(event.get_message()))
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
    await break_dist_calculation.finish(final_msg)


@song_random.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await random_by_aug(str(event.get_message()))
    try:
        await song_random.send(Message([
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
        await song_random.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))


@best_list_query.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await best_list_query.send(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": "ちょっと待ってください〜"}
        }
    ]))
    img, text = await get_best_list(str(event.get_message()), event.user_id)
    final_msg = None
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
        ])
    elif text:
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
    await best_list_query.finish(final_msg)


@chart_random.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await random_chart(str(event.get_message()))
    if img:
        try:
            await chart_random.send(Message([
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
            await chart_random.send(Message([
                {
                    "type": "reply",
                    "data": {"id": event.message_id}
                },
                {
                    "type": "text",
                    "data": {"text": "好像被风控了捏"}
                }]))
    else:
        await chart_random.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "有这位谱师嘛？"}
            }]))


@alias_addition.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await add_alias(str(event.get_message()))
    await alias_addition.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@alias_showing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await find_alias(str(event.get_message()))
    await alias_showing.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@alias_deletion.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await delete_alias(str(event.get_message()))
    await alias_deletion.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }
    ]))


@level_list_showing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await get_level_achievements_list(str(event.get_message()), event.user_id)
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
    await level_list_showing.finish(final_msg)


@level_process_showing.handle()
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
    await level_process_showing.finish(final_msg)


@plate_process_showing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await get_plate_process(str(event.get_message()), event.user_id)
    if text:
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
        await plate_process_showing.send(final_msg)
    await plate_process_showing.finish()


@plate_requirements_showing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await get_ver_plates(str(event.get_message()))
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
    await plate_requirements_showing.finish(final_msg)


@name_plates_viewing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await name_plates_viewing.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "image",
            "data": {
                "file": f"file://{os.getcwd()}/material/plates/list.png"
            }
        }]
    ))


@name_plate_configuration.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await set_name_plate(str(event.get_message()), event.user_id)
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
    await name_plate_configuration.finish(final_msg)


@notes_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await search_by_notes_amount(str(event.get_message()))
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
    text = await search_by_bpm(str(event.get_message()))
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


@rating_analysis.handle()
async def _(bot: Bot, event: Event, state: T_State):
    error, img = await get_rating_analysis(str(event.get_message()), event.user_id)
    if not error:
        await rating_analysis.send(Message([
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
        await rating_analysis.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": error}
            }
        ]))


@achievements_line_calculation.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await get_achievements_line(str(event.get_message()))
    if text:
        await achievements_line_calculation.send(Message([
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
        await achievements_line_calculation.send(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "image",
                "data": {"file": f"base64://{img}"}
            }
        ]))


@stores_finding.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text, img = await find_store(str(event.get_message()))
    if not img:
        await stores_finding.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": text}
            }]))
    else:
        await stores_finding.finish(Message([
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


@store_viewing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = await select_store(str(event.get_message()))
    await store_viewing.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }]))


@rating_line_showing.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = cal_single_rating_line(str(event.get_message()))
    await rating_line_showing.finish(Message([
        {
            "type": "reply",
            "data": {"id": event.message_id}
        },
        {
            "type": "text",
            "data": {"text": text}
        }]))
