import os
from javascript import require, once
from time import sleep


def login(ip, name, version):
    mineflayer = require('mineflayer')
    BOT_USERNAME = name
    if ':' in ip:
        port = int(ip.split(':')[1])
        ip = ip.split(':')[0]
    else:
        port = 25565
    bot = mineflayer.createBot(
        {'host': ip, 'port': port, 'username': BOT_USERNAME, 'hideErrors': True, 'version': version})
    once(bot, 'login')
    return bot


def connectAndSendMessage(messages):
    bot = login('MC.HEROGUILD.GQ:25578', 'Iscariot', '1.18.1')
    sleep(4)
    bot.chat('/l ' + os.environ['minecraft_login'])
    if type(messages) == str:
        messages = [messages]
    for i in messages:
        # bot.chat('/message Filabdict '+ i)
        bot.chat(i)
        sleep(2)

    bot.removeAllListeners('spawn')
    bot.quit()
    bot.end()
    return True
