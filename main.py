#!/usr/bin/env python3

import multiprocessing.connection
import os
import traceback

try:
    import google_sheets
except:
    print(traceback.format_exc())

try:
    if os.environ["its_host"]:
        from gigs import живем

        живем()
except Exception as e:
    print(e)


import mineflayer

import asyncio
import json
import datetime
import re
import copy

# import pysftp
import paramiko  # type: ignore
import threading
import time
import ping
import pymorphy2  # type: ignore
from async_lru import alru_cache  # type: ignore
from functools import lru_cache, wraps
from datetime import timedelta, timezone
import discord
from discord import app_commands
from discord.ext import commands
from num2t4ru import num2text
from time import sleep
import multiprocessing
import sys
import socks

import logging

# Настраиваем логирование


class CustomFormatter(logging.Formatter):
    """Кастомный форматтер для цветного вывода логов."""

    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"
    )

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: grey + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.format)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


# Создаём логгер
logger = logging.getLogger("bot_roles")
logger.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO))

# Создаём StreamHandler и задаём кастомный форматтер
ch = logging.StreamHandler()
ch.setFormatter(CustomFormatter())
logger.addHandler(ch)


for i in ["HG_discord_token"]:
    if i not in os.environ:
        logger.error(f"У вас не объявлена переменная среды '{i}'")
        sys.exit()

discord_token = os.environ["HG_discord_token"]
guild_id = 612339223294640128
"""id сервера"""
correct_name_chanell_id = 1074782370974154803
'''канал, в котором написано "игровое имя - id дискорда"'''
correct_hg_channel_id = 1075091750181421077
"""канал, который база данных для имеющих хг+/++"""
alert_hg_channel_id = 1076249944199008397
"""канал, в который срется команда если зайти на сервер не удалось"""
channel_online_id = 1061084588996300800
"""канал, который счетчик онлайна"""
channel_reaction_id = 1083268762859474974
"""канал, на сообщения в котором люди ставят реакцию для получения роли кураторки"""

intents = discord.Intents.default()
intents.members = True
intents.reactions = True
if "proxy_http" in os.environ:
    client = discord.Client(intents=intents, proxy=os.environ["proxy_http"])
else:
    client = discord.Client(
        intents=intents,
    )
tree_commands = app_commands.CommandTree(client)


all_roles = [  # Все роли и время необходимое для их выдачи
    {
        96: "search:|96+",
        48: "search:|48+",
        36: "search:|36+",
        24: "search:|24+",
        16: "search:|16+",
        12: "search:|12+",
        8: "search:|8+",
        4: "search:|4+",
        2: "search:|2+",
        1: "search:|1+",
        0: "search:|0+",
        -999: "search:Отсутствие онлайна",
    },
    {
        16: "💷HG+",
        24: "💷HG+!",
        36: "💳HG++",
        48: "💳HG++!",
    },
]
hg_roles = {  # Время, на сколько дается каждая роль
    "💷HG+": 5,
    "💷HG+!": 7,
    "💳HG++": 5,
    "💳HG++!": 7,
}
blacklist_roles = (
    [  # Черный список ролей, при наличии которых учатник будет пропускаться
        "Больничный",
        "unverified",
        "Антиквариат",
        "В бане",
        "Бывший Участник",
    ]
)
whitelist_roles = [  # Список ролей, хоть одна из которых должна быть у пользователя
    "Участник",
]
blacklist_users = [
    763478380179226624,
    312657903838429184,
]


__temp__ = []
for i in all_roles:
    __temp__.append(dict(sorted(i.items())))
all_roles = __temp__
del __temp__
all_roles_list = []
del i  # type: ignore


async def setSFTPauth(data: json):
    await client.get_guild(819850729724051456).get_channel(1239528431180582983).send(
        str(data)
    )


async def updateSFTPauth():
    global sftp_auth
    async for message in (
        client.get_guild(819850729724051456)
        .get_channel(1239528431180582983)
        .history(limit=1)
    ):
        sftp_auth = json.loads(
            message.content.replace("`", "").replace("'", '"')
        )  # Получение данных для sftp аутентификации


sftp_auth = {
    "ip": str,
    "portSFTP": int,
    "passwordSFTP": str,
    "usernameSFTP": str,
    "portRCON": int,
    "passwordRCON": str,
}  # Данные для sftp аутентификации


@client.event
async def on_ready():
    global all_roles_list, all_roles, blacklist_roles
    await updateSFTPauth()
    await tree_commands.sync(guild=discord.Object(id=guild_id))
    await client.wait_until_ready()
    getTodayOnTime()
    for role_ds in client.get_guild(guild_id).roles:  # type: ignore
        for i in range(len(blacklist_roles)):
            if blacklist_roles[i] in role_ds.name:
                blacklist_roles[i] = role_ds.name
        for roles in all_roles:
            for key, value in roles.items():
                if value.replace("search:", "") in role_ds.name:
                    roles[key] = role_ds.name
    for i in all_roles:
        for i2 in i.values():
            all_roles_list.append(i2)
    __temp__ = []
    for i in client.get_guild(guild_id).roles:  # type: ignore
        if i.name in all_roles_list:
            __temp__.append(i)
    all_roles_list = __temp__
    del __temp__
    ping_parser = ping.Parser("", 14 / 88)
    time_chanel_edit = 0
    logger.info("Бот запущен!")
    await deleteOutHG()
    await update_roles()
    while not client.is_closed():
        try:
            if True or getNowTime().hour <= 6 and getNowTime().hour >= 1:
                await update_roles()
                logger.info("Все пользователи пущены по кругу")
            online = ping.pingHG(
                ip=sftp_auth["ip"], port=sftp_auth["portGAME"], users=ping_parser
            )
            try:
                google_sheets.append_online_status(getNowTime(), online[1])
            except:
                logger.warning(
                    "Ошибка при попытка заполнить в таблицу онлайн\n"
                    + traceback.format_exc()
                )
            if online[-1]:
                if True or time_chanel_edit + 60 * 10 < time.time():
                    try:
                        await client.change_presence(
                            activity=discord.Game(name=f"HG: {online[0]}/99"),
                            status=discord.Status.online,
                        )
                    except:
                        logger.warning("Ошибка при попытка выставить онлайн в статус")
                    time_chanel_edit = time.time()
                    try:
                        await client.get_channel(channel_online_id).edit(
                            name=f"Онлайн: {online[0]}"
                        )
                    except:
                        logger.warning(
                            "Ошибка при попытка выставить онлайн в название канала"
                        )
        except Exception as e:
            logger.warning(traceback.format_exc())
        await asyncio.sleep(60 * 5)  # раз в #


def thisUserLegitimate(member: discord.Member) -> bool:
    member_roles = [i.name for i in member.roles]
    if member.id in blacklist_users:
        return True
    if max([i not in member_roles for i in whitelist_roles]):
        return False
    return True


def thisUserCanChange(member: discord.Member) -> bool:
    member_roles = [i.name for i in member.roles]
    if max([i in member_roles for i in blacklist_roles]):
        return False
    if max([i not in member_roles for i in whitelist_roles]):
        return False
    if member.id in blacklist_users:
        return False
    if len(member_roles) <= 1:
        return False
    if "НЕВЕРНЫЙ НИК" in member.display_name:
        return False
    # if abs(member.joined_at - datetime.datetime.now()) < datetime.timedelta(hours=12):
    # return False
    return True


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)  # type: ignore
        func.expiration = datetime.datetime.now(timezone.utc) + func.lifetime  # type: ignore

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.datetime.now(timezone.utc) >= func.expiration:  # type: ignore
                func.cache_clear()
                func.expiration = datetime.datetime.now(timezone.utc) + func.lifetime  # type: ignore
            return func(*args, **kwargs)

        return wrapped_func

    return wrapper_cache


def getNowTime(add_days=0) -> datetime.datetime:
    now = datetime.datetime.now(
        tz=datetime.timezone(datetime.timedelta(hours=0))
    ) + datetime.timedelta(days=add_days)
    return now


def addRoles(users: [{"name": str, "time": int, "roles": []}, ...]) -> [{"name": str, "time": int, "roles": [str, ...]}, ...]:  # type: ignore
    users = users.copy()
    for user in users:
        user["roles"] = []
        for unit in all_roles:
            for i in reversed(unit.keys()):
                if round(user["time"]) >= i:
                    user["roles"].append(unit[i])
                    break
    return users


def __treadingWaiting(func, result: [], stop_event: threading.Event, *args) -> None:  # type: ignore
    result.append(func(*args))


def treadingWaiting(time_sleep: int, func, *args):
    def __multiprocessingWaiting(conn, func, args):
        try:
            result = func(*args)
            result = str(result)
            conn.send(result)
        except Exception as e:
            conn.send(e)
        finally:
            conn.close()

    while True:
        parent_conn, child_conn = multiprocessing.Pipe()
        process = multiprocessing.Process(
            target=__multiprocessingWaiting,
            args=(child_conn, func, args),
            name=func.__name__,
            daemon=True,
        )
        process.start()
        process.join(time_sleep)
        if process.is_alive():
            process.terminate()
            process.join()
            time.sleep(3)
            logger.warning(f"Поток {func.__name__} завершен с таймаутом!")
        else:
            result = parent_conn.recv()
            if isinstance(result, Exception):
                raise result
            return result


# @timed_lru_cache(10)
def generateSFTP() -> paramiko.SFTPClient:
    """Генерация SFTP с использованием HTTP/HTTPS-прокси (PySocks)"""
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Проверяем наличие переменной окружения proxy_http
    proxy_http = os.environ.get("proxy_http")
    proxy = None

    if proxy_http:
        try:
            # Парсим прокси-строку
            proxy_url = proxy_http.replace("http://", "").replace("https://", "")
            if "@" in proxy_url:
                # С прокси-аутентификацией
                auth, proxy_address = proxy_url.split("@")
                login, password = auth.split(":")
                proxy_host, proxy_port = proxy_address.split(":")
            else:
                # Без прокси-аутентификации
                login, password = None, None
                proxy_host, proxy_port = proxy_url.split(":")

            # Указываем настройки прокси через PySocks
            proxy = socks.socksocket()
            proxy.set_proxy(
                socks.HTTP,  # Тип прокси (HTTP)
                proxy_host,
                int(proxy_port),
                username=login,
                password=password,
            )
            proxy.connect((sftp_auth["ip"], sftp_auth["portSFTP"]))
            logger.debug(f"Используется прокси: {proxy_http}")
        except Exception as e:
            logger.error(f"Ошибка в настройках переменной окружения proxy_http: {e}")
            raise ValueError(
                "Некорректный формат переменной proxy_http. Ожидается 'http://[login:password@]host:port'"
            )

    while "sftp" not in locals():
        try:
            ssh.connect(
                hostname=sftp_auth["ip"],
                port=sftp_auth["portSFTP"],
                username=sftp_auth["usernameSFTP"],
                password=sftp_auth["passwordSFTP"],
                sock=proxy,  # Передаём прокси-сокет в подключение
                look_for_keys=False,
                allow_agent=False,
            )
            sftp = ssh.open_sftp()
        except Exception as e:
            logger.warning(f"Ошибка подключения по sftp: {e}")
            sleep(5)
    return sftp  # type: ignore


def parsTimeAllUsers() -> [{"name": str, "time": int, "roles": []}, ...]:  # type: ignore
    """Время отдельных людей за все время"""
    all = getAllTimeAndTimeSplitDay().copy()
    return all["allTime"]


def getAllTimeAndTimeSplitDay() -> {"allTime": [{"name": str, "time": int, "roles": []}, ...], "allDayTime": [[{"name": str, "time": int, "roles": []}, ...], ...]}:  # type: ignore
    """Возвращает как время людей за все время ([allTime]), так и не суммированное время ([allDayTime])"""

    def addTime(users: [{"name": str, "time": int, "roles": []}, ...], finnaly: list, all_time_in_days: list):  # type: ignore
        """Изменяет напрямую finnaly и all_time_in_days, которые передаются ему"""
        all_time_in_days.append(copy.deepcopy(users))
        for user in users:
            for i in finnaly:
                if user["name"] == i["name"]:
                    i["time"] += user["time"]
            if user["name"] not in [i["name"] for i in finnaly]:
                finnaly.append(user.copy())

    finnaly = []
    all_time_in_days = []
    addTime(getTodayOnTime().copy(), finnaly, all_time_in_days)
    for i in range(1, 8):
        date = getNowTime(add_days=-1 * i).strftime("%Y.%m.%d")
        users = copy.deepcopy(getDailyOnTime(f"/plugins/OnTime/{date} DailyReport.txt"))
        if i == 7:
            for user in users:
                time1 = user["time"] * ((getNowTime().hour * (100 / 23)) / 100)
                user["time"] = round(user["time"] - time1, 4)
        addTime(users, finnaly, all_time_in_days)
    return {"allTime": finnaly.copy(), "allDayTime": all_time_in_days.copy()}


@timed_lru_cache(10)
def getSFTPfile(patch: str) -> str:
    sftp = generateSFTP()
    table = None
    while not table:
        try:
            table = sftp.open(patch)
            table = table.read()
            table = table.decode()
        except FileNotFoundError as e:
            table = ""
            break
        except Exception as e:
            sleep(60)
    sftp.close()
    del sftp
    # ftp = FTP()
    # ftp.connect("45.87.104.20", 2022)
    # ftp.login(user="", passwd="")
    # temp_file = tempfile.NamedTemporaryFile(delete=False)
    # ftp.retrbinary('RETR patch.txt', temp_file.write)
    # temp_file.seek(0)
    # file_content = temp_file.read()
    # temp_file.close()
    # ftp.quit()
    return table


@timed_lru_cache(60 * 10)
def getTodayOnTime(patch="/plugins/OnTime/playerdata.yml") -> [{"name": str, "time": int, "roles": []}, ...]:  # type: ignore
    """Возвращает время за сегодня, которое в playerdata.yml"""
    playerdata: str = treadingWaiting(8, getSFTPfile, patch)
    users = []
    for slicee in playerdata.split("\n"):
        if ": '" not in slicee:
            continue
        slicee = slicee.split(",")
        name = slicee[1]
        time = int(slicee[4])
        if time > 1000 * 60:
            users.append(
                {
                    "name": name,
                    "time": round(time / 1000 / 60 / 60, 4),
                    "roles": [],
                }
            )
    return users.copy()


@lru_cache
def getDailyOnTime(patch: "/home/2023.02.05.txt") -> [{"name": str, "time": int, "roles": []}, ...]:  # type: ignore
    table = treadingWaiting(8, getSFTPfile, patch)
    users = []
    for slicee in table.split("\n"):
        if "#" not in slicee:
            continue
        slicee = slicee.split("Total:")[0]
        name = re.search(r"[#]\d*\S \S*", slicee)[0].split(" ")[-1]  # type: ignore
        slicee = slicee.split("Today:")[-1]
        day = re.findall(r"\d+ +Day", slicee)
        if len(day) < 1:
            day = 0
        else:
            day = day[0]
            day = int(day.split(" ")[0])
        hr = re.findall(r"\d+ +Hr", slicee)
        if len(hr) < 1:
            hr = 0
        else:
            hr = hr[0]
            hr = int(hr.split(" ")[0])
        min = re.findall(r"\d+ +Min", slicee)
        if len(min) < 1:
            min = 0
        else:
            min = min[0]
            min = int(min.split(" ")[0])
        seconds = re.findall(r"\d+ +Seconds", slicee)
        if len(seconds) < 1:
            seconds = 0
        else:
            seconds = seconds[0]
            seconds = int(seconds.split(" ")[0])
        users.append(
            {
                "name": name,
                "time": round((day * 24) + hr + (min / 60) + (seconds / 60 / 60), 4),
                "roles": [],
            }
        )
    return users


async def deleteOutHG() -> None:
    def check_time(mess):
        return mess.content in delete

    now = int(time.time())
    delete = []
    channel = client.get_channel(correct_hg_channel_id)
    for i in await getLastMessages(correct_hg_channel_id):  # type: ignore
        if int(re.sub(r"\D", "", i.split("-")[2].strip())) < now:
            delete.append(i)
    await channel.purge(check=check_time)  # type: ignore
    return


async def doGiveHG() -> [{"name": str, "role": str, "time": int}]:  # type: ignore
    now = int(time.time())
    messages = []
    for i in await getLastMessages(correct_hg_channel_id):  # type: ignore
        if len(i.split("-")) >= 3:
            messages.append(i)
    people = [
        {
            "name": i.split("-")[0].strip(),
            "role": i.split("-")[1].strip(),
            "time": int(re.sub(r"\D", "", i.split("-")[2].strip())),
        }
        for i in messages
    ]
    haram = []
    for user in people:
        if user["time"] > now:
            haram.append(
                {"name": user["name"], "role": user["role"], "time": user["time"]}
            )
    return haram


@alru_cache(ttl=30)
async def getLastMessages(channel_id: str, raw: bool = False) -> [str, ...]:  # type: ignore
    channel = client.get_channel(channel_id)  # type: ignore
    messages = []
    async for message in channel.history(limit=1000):  # type: ignore
        messages.append(message)
    if raw:
        return messages
    message_list = [m.content for m in messages]
    return message_list


def check_role_HG(hg_correct: [str, ...], role: str) -> bool:  # type: ignore
    hg_list = ["💷HG+", "💷HG+!", "💳HG++", "💳HG++!"]
    if not hg_correct or role not in hg_list or "HG+" not in role:
        return True
    role = role.replace("💷", "").replace("💳", "")
    hg_correct = [i.replace("💷", "").replace("💳", "") for i in hg_correct]
    if role < max(hg_correct):
        return False
    return True


async def setRoles(user: {"name": str, "time": int, "roles": [str, ...]}, member: discord.Member, guild: discord.Guild, hg_correct: [{"name": str, "role": str, "time": int}, ...]) -> None:  # type: ignore
    __temp__ = []
    for i in hg_correct:
        if i["name"] == user["name"]:
            __temp__.append(i["role"])
    __temp__.sort()
    hg_correct = __temp__
    del __temp__
    member_roles = [i.name for i in member.roles]
    if not thisUserCanChange(member):
        return
    elif not await checkCorrectNameInDiscord(member):  # type: ignore
        await member.edit(nick=f"НЕВЕРНЫЙ НИК ({member.display_name})"[:32])
        return
    roles_add = []
    roles_remove = []
    for role_name in user["roles"] + hg_correct:
        if role_name.replace("!", "") not in member_roles and check_role_HG(
            hg_correct, role_name
        ):
            role = discord.utils.get(guild.roles, name=role_name.replace("!", ""))
            if role:
                roles_add.append(role)
            else:
                logger.warning(f"Роль {role_name} не найдена!")
        if (
            role_name not in hg_correct
            and "HG+" in role_name
            and check_role_HG(hg_correct, role_name)
        ):
            give_days = list(hg_roles.values())[list(hg_roles.keys()).index(role_name)]
            await client.get_channel(correct_hg_channel_id).send(  # type: ignore
                f"{user['name']} - {role_name} - <t:{give_days*24*60*60+int(time.time())}:R>"
            )
            role_name = role_name.replace("💳", "").replace("💷", "")
            try:
                mineflayer.connectAndSendMessage(
                    ip=sftp_auth["ip"],
                    port=sftp_auth["portRCON"],
                    password=sftp_auth["passwordRCON"],
                    # ([
                    #     f"/lp user {user['name']} parent removetemp hg+",
                    # ] if 'hg++' in role_name.lower() else [f"/lp user {user['name']} parent removetemp hg++"]) +
                    messages=[
                        f"lp user {user['name']} parent removetemp {role_name.replace('!', '').lower()}",
                        f"lp user {user['name']} parent addtemp {role_name.replace('!', '').lower()} {give_days}d",
                        f"tell {user['name']} вам выдан {role_name.replace('!', '').lower()} на {give_days}d, перезайдите.",
                    ],
                )
                logger.info(f"Успешно (?) выданы роли {role_name}")
            except Exception as e:
                logger.warning(f"Ошибка при выдачи hg+/++: {e}")
                await client.get_channel(alert_hg_channel_id).send(  # type: ignore
                    f"`/lp user {user['name']} parent addtemp {role_name.replace('!', '').lower()} {give_days}d`"
                )
            hg_correct.append(role_name)
    for i in all_roles_list:
        if (i in member.roles and i.name not in user["roles"]) and i.name not in [
            i.replace("!", "") for i in hg_correct
        ]:
            roles_remove.append(i)
    if roles_add or roles_remove:
        logger.info(
            f"	+++ Юзеру {member.display_name} выданы роли \"{'; '.join([i.name for i in roles_add])}\""
            + (
                f" и убраны \"{'; '.join([i.name for i in roles_remove])}\""
                if roles_remove
                else ""
            )
        )
        # return
        for i in roles_remove:
            await member.remove_roles(i)
        for i in roles_add:
            await member.add_roles(i)


@timed_lru_cache(300)
def get_guild(client: discord.client.Client) -> discord.Guild:
    return client.get_guild(guild_id)  # type: ignore


@timed_lru_cache(60)
def getAllMembersInMinecraft(n: None = None) -> [str, ...]:  # type: ignore
    playerdata = treadingWaiting(8 * 2, getSFTPfile, "/whitelist.json")
    playerdata = json.loads(playerdata)
    nicknames = []
    for user in playerdata:
        nicknames.append(user["name"])
    if not nicknames:
        raise Exception("Нет ников игроков, лол")
    return nicknames


async def checkCorrectNameInDiscord(member: discord.User) -> bool:
    # return True
    correct_members = await getCorrectMembers()
    for user in getAllMembersInMinecraft():
        if re.sub(r"[\W]", "", member.display_name).lower() == user.lower() or max(
            [
                (mem["name"] == user and mem["id"] == member.id)
                for mem in correct_members
            ]
        ):
            return True
    return False


@alru_cache(ttl=5)
async def getCorrectMembers() -> [{"name": str, "id": int}, ...]:  # type: ignore
    messages = await getLastMessages(correct_name_chanell_id)  # type: ignore
    correct_members = []
    for message in messages:
        [
            (
                correct_members.append({"name": i.split("-")[0], "id": i.split("-")[1]})
                if len(i.split("-")) > 1
                else None
            )
            for i in message.split("\n")
        ]
    correct_members = [
        {"name": i["name"].strip(), "id": int(i["id"].strip())} for i in correct_members
    ]
    return correct_members


@alru_cache(ttl=1)
async def update_roles(user_need_update: discord.Member = None) -> None:  # type: ignore
    logger.info("Инициирована проверка додиков")
    hg_correct = await doGiveHG()
    users_list = addRoles(parsTimeAllUsers())
    guild = get_guild(client)
    users_list = sorted(users_list, key=lambda user: user["time"], reverse=True)
    correct_members = await getCorrectMembers()
    for member in [user_need_update] if user_need_update else guild.members:
        if member.bot:
            continue
        find = False
        for user in users_list:
            if re.sub(r"[\W]", "", member.display_name).lower() == user[
                "name"
            ].lower() or max(
                [
                    (mem["name"] == user["name"] and mem["id"] == member.id)
                    for mem in correct_members
                ]
            ):
                find = True
                await setRoles(user, member, guild, hg_correct)
        if not find:
            user = [
                {
                    "name": re.sub(r"[\W]", "", member.display_name),
                    "time": -1,
                    "roles": [],
                }
            ]
            await setRoles(addRoles(user)[0], member, guild, hg_correct)
    logger.info("Проверка додиков окончена")


@client.event
async def on_member_update(before, after):
    if not thisUserCanChange(after):
        return
    async for event in before.guild.audit_logs(
        limit=1, action=discord.AuditLogAction.member_role_update
    ):
        if getattr(event.target, "id", None) != before.id:
            continue
        if event.user.id == client.user.id:
            return
    await update_roles(after)


def checkReactionОжидаюКураторки(payload: discord.RawReactionActionEvent, user):
    new_blacklist_roles = blacklist_roles.copy()
    new_blacklist_roles.remove(blacklist_roles[1])
    if payload.channel_id != channel_reaction_id:
        return False
    if max([role in [i.name for i in user.roles] for role in new_blacklist_roles]):
        return False
    if max([role in [i.name for i in user.roles] for role in whitelist_roles]):
        return False
    return True


@timed_lru_cache(100)
async def sendMessageAlertКуратоки(user: discord.User):
    channel = client.get_channel(channel_reaction_id)
    await channel.send(f"<@&918718807227396146> <@{user.id}> хочет пройти кураторку!")  # type: ignore
    return True


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    user = discord.utils.get(client.get_all_members(), id=payload.user_id)
    if checkReactionОжидаюКураторки(payload, user):
        await user.add_roles(discord.utils.get(get_guild(client).roles, name="Ожидаю Кураторки!"))  # type: ignore
        await sendMessageAlertКуратоки(user)  # type: ignore
    elif payload.channel_id == channel_reaction_id:
        channel = client.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)  # type: ignore
        await message.remove_reaction(payload.emoji, user)  # type: ignore


@client.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    user = discord.utils.get(client.get_all_members(), id=payload.user_id)
    if checkReactionОжидаюКураторки(payload, user):
        await user.remove_roles(discord.utils.get(get_guild(client).roles, name="Ожидаю Кураторки!"))  # type: ignore


@client.event
async def on_member_join(member: discord.User):
    await member.add_roles(discord.utils.get(get_guild(client).roles, name=blacklist_roles[1]))  # type: ignore


def listTimeToText(list):
    text = ""
    for i in range(len(list)):
        if list[i] >= 0:
            time1 = list[i]
            text += f"{getNowTime(add_days=-1*(i+0)).strftime('%m.%d')}: {int(time1)}h {int((time1 - int(time1)) * 60)}m\n"
        else:
            text += f"{getNowTime(add_days=-1*(i+0)).strftime('%m.%d')}: ---\n"
    return text


def customLen(str):
    if "HG++!" in str:
        return 4
    if "HG++" in str:
        return 3
    if "💷HG+!" in str:
        return 2
    if "HG+" in str:
        return 1
    return 0


@tree_commands.command(
    name="ontime",
    description="Возвращает ваш онлайн на сервере",
    guild=discord.Object(id=guild_id),
)
async def ontime(interaction: discord.Interaction, name: str = None, invisible: bool = True):  # type: ignore
    await interaction.response.defer(ephemeral=invisible)

    def getNumberAndNoun(numeral, noun):
        try:
            word = pymorphy2.MorphAnalyzer().parse(noun)[0]
            v1, v2, v3 = (
                word.inflect({"sing", "nomn"}),
                word.inflect({"gent"}),
                word.inflect({"plur", "gent"}),
            )
            return num2text(num=numeral, main_units=((v1.word, v2.word, v3.word), "m"))
        except:
            return f"{numeral}h"

    async def getRoleAndTime(username):
        users = await doGiveHG()
        people = []
        for i in users:
            if i["name"].lower() == username.lower():
                people.append(i)
        if people:
            people = sorted(
                people, key=lambda user: customLen(user["role"]), reverse=True
            )[0]
        return people

    def getOnlineUserInDays(name):
        seven_days_user = []
        for i in getAllTimeAndTimeSplitDay()["allDayTime"]:
            t = True
            for i2 in i:
                if i2["name"].lower() == name.lower():
                    seven_days_user.append(i2["time"])
                    t = False
            if t:
                seven_days_user.append(-1)
        return seven_days_user

    correct_members = await getCorrectMembers()
    try:
        time_users = parsTimeAllUsers()
    except:
        sleep(10)
        time_users = parsTimeAllUsers()
    now = int(time.time())
    member = interaction.user
    for user in time_users:
        people = None
        if name:
            if name.lower() == user["name"].lower():
                people = await getRoleAndTime(name)
        elif re.sub(r"[\W]", "", member.display_name).lower() == user[
            "name"
        ].lower() or max(
            [
                (mem["name"] == user["name"] and mem["id"] == member.id)
                for mem in correct_members
            ]
        ):
            name = user["name"]
            people = await getRoleAndTime(user["name"])

        if people != None:
            time1 = user["time"]
            return await interaction.followup.send(
                f"Онлайн `{name}` за семь дней составляет {int(time1)}h {int((time1 - int(time1)) * 60)}m."
                + (
                    f"\n{people['role'].replace('!', '')} кончится <t:{people['time']}:R>."
                    if people and people["time"] >= 0
                    else ""
                )
                + f"```{listTimeToText(getOnlineUserInDays(name))}```"  # type: ignore
            )
    if name:
        return await interaction.followup.send(f"Пользователь {name} не был найден")
    else:
        return await interaction.followup.send(
            "За последние семь дней у тебя не было ни дня онлайна! Извиняться будешь на коленях."
        )


@tree_commands.command(
    name="ontimetop",
    description="Возвращает топ онлайна",
    guild=discord.Object(id=guild_id),
)
async def ontimetop(interaction: discord.Interaction, invisible: bool = True):
    await interaction.response.defer(ephemeral=invisible)
    time_users = parsTimeAllUsers()
    time_users = sorted(time_users, key=lambda user: user["time"], reverse=True)
    topbal = ""
    for i in range(len(time_users[0:15])):
        time1 = time_users[i]["time"]
        topbal += f"{i+1}. {time_users[i]['name']}: {int(time1)}h {int((time1 - int(time1)) * 60)}m\n"
    return await interaction.followup.send(
        f"Топ онлайна за семь дней:```\n{topbal}```||обновляется каждый день в <t:31536000:t>||"
    )


@tree_commands.command(
    name="online",
    description="Возвращает список игроков на сервере",
    guild=discord.Object(id=guild_id),
)
async def online(interaction: discord.Interaction, invisible: bool = True):
    await interaction.response.defer(ephemeral=invisible)
    users = ping.pingHG(ip=sftp_auth["ip"], port=sftp_auth["portGAME"])[1]
    return await interaction.followup.send(
        f"Игроки: `{', '.join(users)}`" if users else "Игроков нет. Что за дела?"
    )


@tree_commands.command(
    name="edit_data",
    description="Изменение данных сервера",
    guild=discord.Object(id=guild_id),
)
async def edit_data(
    interaction: discord.Interaction,
    ip: str = None,
    port_sftp: int = None,
    username_sftp: str = None,
    password_sftp: str = None,
    port_rcon: int = None,
    password_rcon: str = None,
    port_for_game: int = None,
):
    await interaction.response.defer(ephemeral=True)
    if interaction.user.id in [interaction.guild.owner.id, 412834999478386710]:
        new_sftp_auth = sftp_auth
        keys_to_check = [
            ("ip", ip),
            ("portSFTP", port_sftp),
            ("passwordSFTP", password_sftp),
            ("usernameSFTP", username_sftp),
            ("portRCON", port_rcon),
            ("passwordRCON", password_rcon),
            ("portGAME", port_for_game),
        ]
        for key, value in keys_to_check:
            if value != None:
                new_sftp_auth[key] = value
        await setSFTPauth(new_sftp_auth)
        await updateSFTPauth()
        await interaction.followup.send("Успешно")
    else:
        await interaction.followup.send("Еще чего")


# @commands.has_permissions(administrator=True)
@tree_commands.command(
    name="clearall",
    description="Удаляет 100 не закрепленных сообщений",
    guild=discord.Object(id=guild_id),
)
async def clearall(interaction: discord.Interaction):
    def check_pinned(mess):
        return not mess.pinned

    await interaction.response.defer(ephemeral=True)
    if not max([i.permissions.administrator for i in interaction.user.roles]):  # type: ignore
        return await interaction.followup.send("Вы не достойны")
    messages = await getLastMessages(interaction.channel_id, raw=True)  # type: ignore
    if len(messages) >= 500:
        return await interaction.followup.send(
            "Сообщений подозрительно много, отказываюсь"
        )
    await interaction.channel.purge(check=check_pinned)  # type: ignore
    return await interaction.followup.send("Сообщения удалены")


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        msg = "Эта команда на кулдауне. Попробуйте снова через {:.2f} секунд.".format(
            error.retry_after
        )
        await ctx.send(msg)
    else:
        raise error


while True:
    client.run(discord_token, log_handler=ch)

    sleep(5)
