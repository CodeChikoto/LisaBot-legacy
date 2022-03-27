import aiohttp
from tools.shared_var import *


async def get_player_data(payload: dict, proj: str):
    try:
        if proj == 'best':
            p = 'player'
        elif proj == 'plate':
            p = 'plate'
        else:
            return '项目错误'
        async with aiohttp.request('POST', f'https://www.diving-fish.com/api/maimaidxprober/query/{p}', json=payload) as resp:
            if resp.status == 400:
                data = "真的有这位玩家嘛？或者是没有绑定 QQ 号？"
            elif resp.status == 403:
                data = '这位好像不给获取信息捏。'
            elif resp.status == 200:
                data = await resp.json()
            else:
                data = '发生了错误，找找机修看看吧'
    except Exception:
        data = '发生了错误，找找机修看看吧'
    return data


def get_all_request_versions() -> list:
    ans = []
    for ver_alias in version_alias.keys():
        ans += version_alias[ver_alias][2]
    return list(set(ans))