import struct
import socket
import base64
import json
import threading
import socks, os


class Server:
    def __init__(self, data):
        self.description = data.get("description")
        if isinstance(self.description, dict):
            self.description = self.description["text"]

        self.icon = base64.b64decode(data.get("favicon", "")[22:])
        self.players = Players(data["players"])
        try:
            self.modinfo = Mods(data["modinfo"])
        except Exception:
            self.modinfo = None
        self.version = data["version"]["name"]
        self.protocol = data["version"]["protocol"]

    def __str__(self):
        return (
            "Server(description={!r}, icon={!r}, version={!r}, "
            "protocol={!r}, players={}, mods={})".format(
                self.description,
                bool(self.icon),
                self.version,
                self.protocol,
                self.players,
                self.modinfo,
            )
        )


class Players(list):
    def __init__(self, data):
        super().__init__(Player(x) for x in data.get("sample", []))
        self.max = data["max"]
        self.online = data["online"]

    def __str__(self):
        return "[{}, online={}, max={}]".format(
            ", ".join(str(x) for x in self), self.online, self.max
        )


class Player:
    def __init__(self, data):
        self.id = data["id"]
        self.name = data["name"]

    def __str__(self):
        return self.name


class Mods(list):
    def __init__(self, data):
        self.type = data["type"]
        self.list = [Mod(x) for x in data.get("modList", [])]

    def __str__(self):
        return "[type={}, list=[{}]]".format(
            self.type, ", ".join(str(x) for x in self.list)
        )


class Mod:
    def __init__(self, data):
        self.modid = data["modid"]
        self.version = data["version"]

    def __str__(self):
        return "{} (Version: {})".format(self.modid, self.version)


def ping(ip, port, buf):
    def read_var_int():
        i = 0
        j = 0
        while True:
            k = sock.recv(1)
            if not k:
                return 0
            k = k[0]
            i |= (k & 0x7F) << (j * 7)
            j += 1
            if j > 5:
                raise ValueError("var_int too big")
            if not (k & 0x80):
                return i

    # Проверяем наличие переменной окружения proxy_http
    proxy_http = os.environ.get("proxy_http")
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

            # Создаем сокет с использованием PySocks
            sock = socks.socksocket()
            sock.set_proxy(
                proxy_type=socks.HTTP,
                addr=proxy_host,
                port=int(proxy_port),
                username=login,
                password=password,
            )
            # print(f"Используется прокси: {proxy_http}")
        except Exception as e:
            print(f"Ошибка в настройках переменной окружения proxy_http: {e}")
            raise ValueError(
                "Некорректный формат переменной proxy_http. Ожидается 'http://[login:password@]host:port'"
            )
    else:
        # Без прокси
        sock = socket.socket()

    # Настройка сокета и подключение
    sock.settimeout(15)
    sock.connect((ip, port))
    sock.settimeout(None)

    try:
        host = ip.encode("utf-8")
        data = b""  # wiki.vg/Server_List_Ping
        data += b"\x00"  # packet ID
        data += b"\x04"  # protocol variant
        data += struct.pack(">b", len(host)) + host
        data += struct.pack(">H", port)
        data += b"\x01"  # next state
        data = struct.pack(">b", len(data)) + data
        sock.sendall(data + b"\x01\x00")  # handshake + status ping
        length = read_var_int()  # full packet length
        if length < 10:
            if length < 0:
                raise ValueError("negative length read")
            else:
                raise ValueError("invalid response %s" % sock.read(length))

        sock.recv(1)  # packet type, 0 for pings
        length = read_var_int()  # string length
        data = b""
        while len(data) != length:
            chunk = sock.recv(length - len(data))
            if not chunk:
                raise ValueError("connection aborted")

            data += chunk
        buf.append(json.loads(data))
        return json.loads(data)
    finally:
        sock.close()


class Parser:
    def __init__(self, people, online):
        self.people = people
        self.online = online

    def main(self, people, online):
        if self.people == people:
            return False
        else:
            # self.people = people
            # self.online = online
            return True


def pingHG(ip: str, port: int, users=Parser("", 1488)) -> (int, list, bool):  # type: ignore
    try:
        data = []
        stop_event = threading.Event()
        t = threading.Thread(target=ping, args=(ip, int(port), data))
        t.start()
        t.join(9)
        if t.is_alive():
            stop_event.set()
            try:
                t._stop()
            except:
                pass
            print("Умер ваш ping")
            try:
                del t
            except:
                pass
        # ping('MC.HEROGUILD.GQ', port=25578)['players']
        data = data[-1]["players"]
    except Exception:
        return -1, ["error connect"], False
    online = int(data["online"])
    try:
        people = [i["name"] for i in data["sample"]]
    except Exception:
        people = []
    people.sort()
    # people = ', '.join(people)
    if users.main(people, online):
        users.online = online
        users.people = people
        return online, people, True
    return online, people, False
