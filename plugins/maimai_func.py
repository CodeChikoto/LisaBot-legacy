from nonebot import on_command, on_regex, on_notice
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Message, Event, Bot
from plugins.send_help import *
from maimai.song_func import *
from interact.cal_luck import *
from interact.emoji import *
from maimai.chart_func import *
from maimai.best_40 import generate
from tools.image import *
import os
import re
from typing import *

base_search = on_command('base_search ', aliases={'定数查歌 '})


@base_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    args = str(event.get_message())
    # Example: 12.0, 黄10.0
    try:
        if args[0].isnumeric():
            msg = search_by_base(float(args[0]))
        else:
            msg = search_by_base(float(args[1:]), args[0])
        await base_search.finish(msg)
    except IndexError:
        await base_search.finish(send_help("base_search"))


level_search = on_command('level_search ', aliases={'等级查歌 '})


@level_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    # Example: 12+, 黄10+,
    args = str(event.get_message())
    if args:
        if args[0].isnumeric():
            msg = search_by_level(args)
        else:
            msg = search_by_level(args[1:], args[0])
        await level_search.finish(msg)
    else:
        await level_search.finish(send_help("level_search"))


name_search = on_command('name_search ', aliases={'查歌 ', "search "})


@name_search.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = search_by_name(str(event.get_message()))
    await name_search.finish(msg)


view_song = on_command('view_song ', aliases={'id '})


@view_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = select_song(str(event.get_message()))
    await view_song.send(msg)


view_chart = on_command("view_chart ", aliases={"查谱 ", "看谱 "})


@view_chart.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        user_in = str(event.get_message())
        msg = select_chart(user_in[1:], user_in[0])
        try:
            file = f"file://{os.getcwd()}/cover/{user_in[1:]}.jpg"
            final_msg = Message([
                {
                    "type": "image",
                    "data": {"file": f"{file}"}
                },
                {
                    "type": "text",
                    "data": {"text": msg}
                }
            ])
        except FileNotFoundError:
            final_msg = msg
    except IndexError:
        final_msg = "谱面不存在或输入有误！"
    await view_song.send(final_msg)


mai_what = on_regex(r".*mai.*什么")


@mai_what.handle()
async def _(bot: Bot, event: Event, state: T_State):
    msg = random_song()
    await view_song.send(msg)


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


async def _group_poke(bot: Bot, event: Event, state: dict) -> bool:
    value = (event.notice_type == "notify" and event.sub_type == "poke" and
             event.target_id == int(bot.self_id))
    return value


random.seed(time.time())
poke_back = on_notice(rule=_group_poke, priority=10, block=True)


@poke_back.handle()
async def _(bot: Bot, event: Event, state: T_State):
    rand = random.randint(1, 10)
    if 1 <= rand <= 3:
        await poke_back.finish(hit_person())
    elif 4 <= rand <= 9:
        if event.__getattribute__('group_id') is None:
            event.__delattr__('group_id')
        await poke_back.send(Message([
            {
                "type": "poke",
                "data": {"qq": f"{event.sender_id}"}
            }]
        ))
    else:
        await poke_back.finish()


which_is = on_regex(r".+是什么歌")


@which_is.handle()
async def _(bot: Bot, event: Event, state: T_State):
    regex = "(.+)是什么歌"
    name = re.match(regex, str(event.get_message())).groups()[0].strip().lower()
    msg = search_by_name(name)
    await name_search.finish(msg)


calculator = on_command("cal ", aliases={"计算器 ", "cal "})


@calculator.handle()
async def _(bot: Bot, event: Event, state: T_State):
    try:
        user_data = str(event.get_message()).split()
        msg = cal_ratio(user_data[0], user_data[1:])
        await calculator.finish(msg)
    except IndexError:
        await calculator.finish(send_help("calculator"))


rule_random_song = on_command("rand_song ", aliases={"随歌 "})


# 红12.8，12.8，12+
@rule_random_song.handle()
async def _(bot: Bot, event: Event, state: T_State):
    user_in, difficulty = str(event.get_message()), '%'
    try:
        if not user_in[0].isnumeric():
            difficulty = user_in[0]
            user_in = user_in[1:]
        if '.' in user_in:
            msg = random_song(difficulty=difficulty, base=user_in)
        else:
            msg = random_song(difficulty=difficulty, level=user_in)
        await rule_random_song.finish(msg)
    except IndexError:
        await rule_random_song.finish(send_help("random_song"))


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


help = on_command("help", aliases={"help", "bot帮助"})


@help.handle()
async def _(bot: Bot, event: Event, state: T_State):
    await help.finish(send_help("help"))