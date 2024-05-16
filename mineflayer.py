import os, json
from time import sleep
import mcrcon


def connectAndSendMessage(ip: str, port: int, password: str, messages: list):
    port = int(port)
    connect = mcrcon.MCRcon(host=ip, port=port, password=password)
    connect.connect()
    if type(messages) == str:
        messages = [messages]
    for command in messages:
        print(f"{command}: {connect.command(command)}")
    connect.disconnect()
    sleep(1)
    return True
