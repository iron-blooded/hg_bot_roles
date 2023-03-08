import os
try:
    if os.environ['its_host']:
        import mineflayer
        from gigs import живем
        живем()
except Exception:
    pass


import discord
import asyncio
import json
import datetime
import re
# import pysftp
import paramiko
import threading
import logging
import time
import ping
import pymorphy2
from async_lru import alru_cache
from functools import lru_cache, wraps
from datetime import timedelta
from discord import app_commands
from num2t4ru import num2text
from time import sleep


discord_token = os.environ['HG_discord_token']
guild_id = 612339223294640128
correct_name_chanell_id = 1074782370974154803
correct_hg_channel_id = 1075091750181421077
alert_hg_channel_id = 1076249944199008397
channel_online_id = 1061084588996300800

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents,)
tree_commands = app_commands.CommandTree(client)


sftp_auth = json.loads(os.environ['HG_sftp_auth'].replace(
    "'", '"'))  # Данные для sftp аутентификации
all_roles = [  # Все роли и время необходимое для их выдачи
    {
        96: 'Величайший Онлайн | 96+',
        48: 'Великий Онлайн | 48+',
        36: 'Вселенский Онлайн | 36+',
        24: 'Галактус|24+',
        16: 'Космический Онлайн|16+',
        12: 'Хороший Онлайн|12+',
        6: 'Нормальный Онлайн |6+',
        4: 'Плохой Онлайн|4+',
        2: 'Ужасный Онлайн|2+',
        0: 'Мракобесие|0+',
        -999: 'Отсутствие онлайна',
    },
    {
        16: 'HG+',
        24: 'HG+!',
        36: 'HG++',
        48: 'HG++!',
    }
]
hg_roles = {  # Время, на сколько дается каждая роль
    'HG+': 9,
    'HG+!': 11,
    'HG++': 9,
    'HG++!': 11,
}
blacklist_roles = [  # Черный список ролей, при наличии которых учатник будет пропускаться
    'Больничный',
    'unverified',
    'Антиквариат',
    'В бане',
    'Бывший Участник',
]
whitelist_roles = [  # Список ролей, хоть одна из которых должна быть у пользователя
    'Участник',
]


__temp__ = []
for i in all_roles:
    __temp__.append(dict(sorted(i.items())))
all_roles = __temp__
del __temp__
all_roles_list = []
for i in all_roles:
    for i2 in i.values():
        all_roles_list.append(i2)
del i


def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = timedelta(seconds=seconds)
        func.expiration = datetime.datetime.utcnow() + func.lifetime

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if datetime.datetime.utcnow() >= func.expiration:
                func.cache_clear()
                func.expiration = datetime.datetime.utcnow() + func.lifetime
            return func(*args, **kwargs)
        return wrapped_func
    return wrapper_cache


def getNowTime(add_days=0) -> datetime.datetime:
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(
        hours=0))) + datetime.timedelta(days=add_days)
    return now


def addRoles(users: [{'name': str, 'time': int, 'roles': []}, ...]) -> [{'name': str, 'time': int, 'roles': [str, ...]}, ...]:
    for user in users:
        for unit in all_roles:
            for i in reversed(unit.keys()):
                if user['time'] >= i:
                    user['roles'].append(unit[i])
                    break
    return users


def __treadingWaiting(func, result: [], stop_event: threading.Event, *args) -> None:
    result.append(func(*args))


def treadingWaiting(time_sleep: int, func, *args):
    result = []
    while result == []:
        stop_event = threading.Event()
        t = threading.Thread(target=__treadingWaiting,
                             args=(func, result, stop_event, *args), name=func.__name__, daemon=True)
        t.start()
        t.join(time_sleep)
        if t.is_alive():
            stop_event.set()
            try:
                t._stop()
            except:
                pass
            try:
                del t
            except:
                pass
            sleep(3)
    return result[-1]


# @timed_lru_cache(10)
def generateSFTP() -> paramiko.client.SSHClient.open_sftp:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    while 'sftp' not in locals():
        try:
            ssh.connect(sftp_auth['ip'], port=sftp_auth['port'], username=sftp_auth['username'],
                        password=sftp_auth['password'])
            sftp = ssh.open_sftp()
        except:
            pass
    return sftp


@timed_lru_cache(60*30)
def parsTimeUsers() -> [{'name': str, 'time': int, 'roles': []}, ...]:
    # sftp = generateSFTP()
    finnaly = []
    for i in range(1, 8):
        date = getNowTime(add_days=-1*i).strftime('%Y.%m.%d')
        users = getDailyOnTime(f'/plugins/OnTime/{date} DailyReport.txt')
        for user in users:
            for i in finnaly:
                if user['name'] == i['name']:
                    i['time'] = i['time'] + user['time']
            if user['name'] not in [i['name'] for i in finnaly]:
                finnaly.append(user)
    # sftp.close()
    for i in finnaly:
        i['time'] = round((i['time']))
    return finnaly


def getSFTPfile(patch: str) -> str:
    sftp = generateSFTP()
    table = sftp.open(patch)
    table = table.read()
    table = table.decode()
    sftp.close()
    del sftp
    return table


def getDailyOnTime(patch: '/home/2023.02.05.txt') -> [{'name': str, 'time': int, 'roles': []}, ...]:
    table = treadingWaiting(8, getSFTPfile, patch)
    users = []
    for slicee in table.split('\n'):
        if '#' not in slicee:
            continue
        slicee = slicee.split('Total:')[0]
        name = re.search(r"[#]\d*\S \S*", slicee)[0].split(' ')[-1]
        day = re.findall(r'\d+ +Day', slicee)
        if len(day) < 1:
            day = 0
        else:
            day = day[0]
            day = int(day.split(' ')[0])
        hr = re.findall("\d+ +Hr", slicee)
        if len(hr) < 1:
            hr = 0
        else:
            hr = hr[0]
            hr = int(hr.split(' ')[0])
        min = re.findall(r"\d+ +Min", slicee)
        if len(min) < 1:
            min = 0
        else:
            min = min[0]
            min = int(min.split(' ')[0])
        seconds = re.findall(r"\d+ +Seconds", slicee)
        if len(seconds) < 1:
            seconds = 0
        else:
            seconds = seconds[0]
            seconds = int(seconds.split(' ')[0])
        users.append({'name': name, 'time': round(
            (day*24)+hr+(min/60)+(seconds/60/60), 4), 'roles': []})
    return users


async def doGiveHG() -> [{'name': str, 'role': str, 'time': int}]:
    now = int(time.time())
    messages = []
    for i in await getLastMessages(correct_hg_channel_id):
        if len(i.split('-')) > 1:
            messages.append(i)
    people = [{'name': i.split('-')[0].strip(), 'role': i.split('-')
               [1].strip(), 'time': int(i.split('-')[2].strip())} for i in messages]
    haram = []
    for user in people:
        if user['time'] > now:
            haram.append(
                {'name': user['name'], 'role': user['role'], 'time': user['time']})
    return haram


@alru_cache(ttl=30)
async def getLastMessages(channel_id: str) -> [str, ...]:
    channel = client.get_channel(channel_id)
    messages = []
    async for message in channel.history(limit=1000):
        messages.append(message)
    message_list = [m.content for m in messages]
    return message_list


def check_role_HG(hg_correct: [str, ...], role: str) -> bool:
    hg_list = ['HG+', 'HG+!', 'HG++', 'HG++!']
    if not hg_correct or role not in hg_list or 'HG+' not in role:
        return True
    if role < max(hg_correct):
        return False
    return True


async def setRoles(user: {'name': str, 'time': int, 'roles': [str, ...]}, member: discord.Member, guild: discord.Guild, hg_correct: [{'name': str, 'role': str, 'time': int}, ...]) -> None:
    __temp__ = []
    for i in hg_correct:
        if i['name'] == user['name']:
            __temp__.append(i['role'])
    __temp__.sort()
    hg_correct = __temp__
    del __temp__
    member_roles = [i.name for i in member.roles]
    if max([i in member_roles for i in blacklist_roles]) \
            or max([i not in member_roles for i in whitelist_roles]) \
            or len(member_roles) <= 1 \
            or 'НЕВЕРНЫЙ НИК' in member.display_name:
        return
    elif not await checkCorrectNameInDiscord(member):
        await member.edit(nick=f'НЕВЕРНЫЙ НИК ({member.display_name})'[:32])
    roles_add = []
    roles_remove = []
    for role_name in user['roles'] + hg_correct:
        if role_name.replace('!', '') not in member_roles and check_role_HG(hg_correct, role_name):
            role = discord.utils.get(
                guild.roles, name=role_name.replace('!', ''))
            if role:
                roles_add.append(role)
            else:
                print(f'Роль {role_name} не найдена!')
        if role_name not in hg_correct and 'HG+' in role_name and check_role_HG(hg_correct, role_name):
            give_days = list(hg_roles.values())[list(
                hg_roles.keys()).index(role_name)]
            try:
                mineflayer.connectAndSendMessage(
                    ([
                        f"/lp user {user['name']} parent removetemp hg+",
                    ] if 'hg++' in role_name.lower() else []) +
                    [
                        f"/lp user {user['name']} parent removetemp {role_name.replace('!', '').lower()}",
                        f"/lp user {user['name']} parent addtemp {role_name.replace('!', '').lower()} {give_days}d",
                    ]
                )
                print(f'Успешно (?) выданы роли {role_name}')
            except:
                await client.get_channel(alert_hg_channel_id).send(
                    f"`/lp user {user['name']} parent addtemp {role_name.replace('!', '').lower()} {give_days}d`")
            await client.get_channel(correct_hg_channel_id).send(
                f"{user['name']} - {role_name} - {give_days*24*60*60+int(time.time())}")
            hg_correct.append(role_name)
    for i in all_roles_list:
        if (i in member.roles and i.name not in user['roles']) and i.name not in [i.replace('!', '') for i in hg_correct]:
            roles_remove.append(i)
    if roles_add or roles_remove:
        print(
            f"	+++ Юзеру {member.display_name} выданы роли \"{'; '.join([i.name for i in roles_add])}\"" + (f" и убраны \"{'; '.join([i.name for i in roles_remove])}\"" if roles_remove else ""))
        for i in roles_remove:
            await member.remove_roles(i)
        for i in roles_add:
            await member.add_roles(i)


@timed_lru_cache(300)
def get_guild(client: discord.client.Client) -> discord.Guild:
    return client.get_guild(guild_id)


@timed_lru_cache(30)
def getAllMembersInMinecraft() -> [str, ...]:
    playerdata = treadingWaiting(
        8, getSFTPfile, '/plugins/PlayTime/userdata.json')
    playerdata = json.loads(playerdata)
    nicknames = []
    for user in playerdata:
        nicknames.append('lastName')
    return nicknames

async def checkCorrectNameInDiscord(member: discord.User) -> bool:
    correct_members = await getCorrectMembers()
    for user in getAllMembersInMinecraft():
        if re.sub("[\W]", "", member.display_name).lower() == user.lower() \
                or max([(mem['name'] == user and mem['id'] == member.id) for mem in correct_members]):
            return True
    return False


@alru_cache(ttl=5)
async def getCorrectMembers() -> [{'name': str, 'id': int}, ...]:
    messages = await getLastMessages(correct_name_chanell_id)
    correct_members = []
    for message in messages:
        [correct_members.append(
            {'name': i.split('-')[0], 'id': i.split('-')[1]}
        ) if len(i.split('-')) > 1 else None for i in message.split('\n')]
    correct_members = [{'name': i['name'].strip(), 'id': int(i['id'].strip())}
                       for i in correct_members]
    return correct_members


@alru_cache(ttl=1)
async def update_roles(user_need_update=None) -> None:
    print('Инициирована проверка додиков')
    hg_correct = await doGiveHG()
    users_list = addRoles(parsTimeUsers())
    guild = get_guild(client)
    users_list = sorted(
        users_list, key=lambda user: user['time'], reverse=True)
    correct_members = await getCorrectMembers()
    for member in ([user_need_update] if user_need_update else guild.members):
        if member.bot:
            continue
        find = False
        for user in users_list:
            if re.sub("[\W]", "", member.display_name).lower() == user['name'].lower() \
                    or max([(mem['name'] == user['name'] and mem['id'] == member.id) for mem in correct_members]):
                find = True
                await setRoles(user, member, guild, hg_correct)
        if not find:
            user = [
                {'name': re.sub("[\W]", "", member.display_name), 'time': -1, 'roles': []}]
            await setRoles(addRoles(user)[0], member, guild, hg_correct)
    print('Проверка додиков окончена')


@client.event
async def on_ready():
    global all_roles_list
    __temp__ = []
    for i in client.get_guild(guild_id).roles:
        if i.name in all_roles_list:
            __temp__.append(i)
    all_roles_list = __temp__
    del __temp__
    ping_parser = ping.Parser('', 14/88)
    time_chanel_edit = 0
    await tree_commands.sync(guild=discord.Object(id=guild_id))
    print('Бот запущен!')
    await client.wait_until_ready()
    while not client.is_closed():
        await update_roles()
        print('Все пущены по кругу')
        online = ping.pingHG(ping_parser)
        if online[-1]:
            if time_chanel_edit + 60*10 < time.time():
                activity = discord.Game(name=f"HG: {online[0]}/99")
                await client.change_presence(activity=activity, status=discord.Status.online)
                time_chanel_edit = time.time()
                await client.get_channel(channel_online_id).edit(name=f"Онлайн: {online[0]}")
        await asyncio.sleep(60*2)  # раз в #


@client.event
async def on_member_update(before, after):
    if max([i in [j.name for j in after.roles] for i in blacklist_roles]) \
            or max([i not in [j.name for j in after.roles] for i in whitelist_roles]) \
            or len(after.roles) <= 1:
        return
    await update_roles(after)


@tree_commands.command(name="ontime", description="Возвращает ваш онлайн на сервере", guild=discord.Object(id=guild_id))
async def ontime(interaction: discord.Interaction, name: str = None, invisible: bool = True):
    await interaction.response.defer(ephemeral=invisible)

    def getNumberAndNoun(numeral, noun):
        word = pymorphy2.MorphAnalyzer().parse(noun)[0]
        v1, v2, v3 = word.inflect({'sing', 'nomn'}), word.inflect(
            {'gent'}), word.inflect({'plur', 'gent'})
        return num2text(num=numeral, main_units=((v1.word, v2.word, v3.word), 'm'))

    async def getRoleAndTime(username):
        users = await doGiveHG()
        people = []
        for i in users:
            if i['name'].lower() == username.lower():
                people.append(i)
        if people:
            people = sorted(
                people, key=lambda user: user['role'], reverse=True)[0]
        return people

    correct_members = getCorrectMembers()
    try:
        time_users = parsTimeUsers()
    except:
        sleep(10)
        time_users = parsTimeUsers()
    now = int(time.time())
    member = interaction.user
    for user in time_users:
        if name:
            if re.sub("[\W]", "", name).lower() == user['name'].lower():
                people = await getRoleAndTime(name)
                return await interaction.followup.send(f"Онлайн `{name}` за семь дней составляет {getNumberAndNoun(int(user['time']), 'час')}." +
                                                       (f"\n{people['role'].replace('!', '')} осталось на {getNumberAndNoun(round((people['time'] - time.time())/60/60/24), 'день')}." if people and people['time'] >= 0 else ""))
        elif re.sub("[\W]", "", member.display_name).lower() == user['name'].lower() \
                or max([(mem['name'] == user['name'] and mem['id'] == member.id) for mem in correct_members]):
            people = await getRoleAndTime(user['name'])
            return await interaction.followup.send(f"Ваш онлайн за семь дней составляет {getNumberAndNoun(int(user['time']), 'час')}." +
                                                   (f"\n{people['role'].replace('!', '')} у вас осталось на {getNumberAndNoun(round((people['time'] - time.time())/60/60/24), 'день')}." if people and people['time'] >= 0 else ""))
    if name:
        return await interaction.followup.send(f"Пользователь {name} не был найден")
    else:
        return await interaction.followup.send("За последние семь дней у тебя не было ни дня онлайна! Извиняться будешь на коленях.")


@tree_commands.command(name="ontimetop", description="Возвращает топ онлайна", guild=discord.Object(id=guild_id))
async def ontimetop(interaction: discord.Interaction, invisible: bool = True):
    await interaction.response.defer(ephemeral=invisible)
    time_users = parsTimeUsers()
    time_users = sorted(
        time_users, key=lambda user: user['time'], reverse=True)
    topbal = ''
    for i in range(len(time_users[0:15])):
        topbal += f"{i+1}. {time_users[i]['name']}: {time_users[i]['time']}h\n"
    return await interaction.followup.send(f"Топ онлайна за семь дней:```\n{topbal}```||обновляется каждый день в 3 ночи по МСК, или в 2 по Киевскому||")


@tree_commands.command(name="online", description="Возвращает список игроков на сервере", guild=discord.Object(id=guild_id))
async def online(interaction: discord.Interaction, invisible: bool = True):
    await interaction.response.defer(ephemeral=invisible)
    users = ping.pingHG()[1]
    return await interaction.followup.send(f"Игроки: `{', '.join(users)}`" if users else "Игроков нет. Что за дела?")


while True:
    client.run(discord_token)
    sleep(5)
