import nonebot
from nonebot import *
from nonebot.adapters.cqhttp import *
from nonebot.adapters.cqhttp.bot import *
from nonebot.rule import Rule, ArgumentParser
from nonebot.typing import *
import re
from pydantic import BaseSettings, validator
from copy import deepcopy
from interact_func.selector import *
from interact_func.send_help import *
from os import *


class Config(BaseSettings):
    command: str = "lisa"
    aliases: set = {"妈妈", "リサ"}
    command_help: set = {"help", "帮助"}
    command_select = {"or", "还是", "或者"}
    command_affection = {"抱抱", "亲亲"}
    command_goodnight = {"我睡觉了", "我要睡了", "晚安", "おやすみ", "お休み"}
    command_mute = {"烟人模式", "禁言模式"}
    command_kick = {"杀人模式", "踢人模式"}
    command_interact = {"打水漂", "抽签", "夏洛缇"}
    command_protect_id = {993433577, 2163947224, 342887476}
    _config: Any = deepcopy(nonebot.get_driver().config)


async def _at_called(bot: Bot, event: Event, state: dict) -> bool:
    return event.is_tome() and not str(event.get_message())


mute_list, mute_time = [], 864000
config = Config()
called = on_shell_command(cmd=config.command, aliases=config.aliases, parser=ArgumentParser(), block=True)
at_called = on_message(rule=_at_called)


async def help_handle(bot: Bot, event: Event, state: T_State):
    argv = state["argv"]
    if argv[0] in config.command_help:
        await called.finish(send_help("help"))


async def select_handle(bot: Bot, event: Event, state: T_State):
    argv = state["argv"]
    if any(keyword in " ".join(argv) for keyword in config.command_select):
        await called.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": auto_select(" ".join(argv))}
            }
        ]))


async def affection_handle(bot: Bot, event: Event, state: T_State):
    argv = state["argv"]
    if argv[0] in config.command_affection:
        await called.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": argv[0] + '！'}
            }
        ]))


async def goodnight_handle(bot: Bot, event: Event, state: T_State):
    argv = state["argv"]
    if argv[0] in config.command_goodnight:
        await called.finish(Message([
            {
                "type": "reply",
                "data": {"id": event.message_id}
            },
            {
                "type": "text",
                "data": {"text": "お休み！"}
            }
        ]))


async def setup_mute(bot: Bot, event: Event, state: T_State):
    global mute_time
    argv = state["argv"]
    if argv[0] in ["禁言", "烟人模式"]:
        user_id = event.user_id
        if user_id == 993433577:
            if len(argv) == 2:
                if argv[1] in ["1", "on", "启动", "始まる"]:
                    mute_time = argv[2] if len(argv) == 3 and argv[2].isdigit \
                        else mute_time
                    mute_list.append(event.group_id)
                    await called.send(Message([
                        {
                            "type": "reply",
                            "data": {"id": event.message_id}
                        },
                        {
                            "type": "text",
                            "data": {"text": "はい〜"}
                        }
                    ]))
                elif argv[1] in ["0", "off", "关闭", "閉まる"]:
                    mute_list.remove(event.group_id)


async def retell(bot: Bot, event: Event, state: T_State):
    argv = state["argv"]
    if any(re.search(keyword, argv[0]) for keyword in config.command_interact) \
            and event.user_id == 993433577:
        await called.finish(argv[0])


async def protect(bot: Bot, event: Event, state: T_State):
    argv = state["argv"][0]
    groups = re.match("(.+)欺负我", argv).groups()
    rand_int = random.randint(0, 1)
    if rand_int == 0:
        await called.finish(groups[0] + "、だめですよ！")
    elif rand_int == 1:
        img_file = f"file://{getcwd()}/emoji/hit/hit3.PNG"
        await called.finish(Message([
            {
                "type": "text",
                "data": {"text": groups[0] + "过来给妈妈梆"}
            },
            {
                "type": "image",
                "data": {"file": f"{img_file}"}
            }
        ]))


@at_called.handle()
async def _(bot: Bot, event: Event, state: T_State):
    pass


called.handle()(help_handle)
called.handle()(affection_handle)
called.handle()(select_handle)
called.handle()(goodnight_handle)
called.handle()(setup_mute)
called.handle()(retell)
called.handle()(protect)