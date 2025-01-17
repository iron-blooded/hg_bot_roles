import os, json
from time import sleep
import os
import socket
import ssl
import select
import struct
import time
import platform, socks

if platform.system() != "Windows":
    import signal


def connectAndSendMessage(ip: str, port: int, password: str, messages: list):
    port = int(port)
    connect = MCRcon(host=ip, port=port, password=password)
    connect.connect()
    if type(messages) == str:
        messages = [messages]
    for command in messages:
        print(f"{command}: {connect.command(command)}")
    connect.disconnect()
    sleep(1)
    return True


class MCRconException(Exception):
    pass


def timeout_handler(signum, frame):
    raise MCRconException("Connection timeout error")


class MCRcon(object):
    """A client for handling Remote Commands (RCON) to a Minecraft server."""

    socket = None

    def __init__(self, host, password, port=25575, tlsmode=0, timeout=5):
        self.host = host
        self.password = password
        self.port = port
        self.tlsmode = tlsmode
        self.timeout = timeout
        if platform.system() != "Windows":
            signal.signal(signal.SIGALRM, timeout_handler)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, type, value, tb):
        self.disconnect()

    def connect(self):
        proxy_http = os.environ.get("proxy_http")
        if proxy_http:
            try:
                # Parse the proxy URL
                proxy_url = proxy_http.replace("http://", "").replace("https://", "")
                if "@" in proxy_url:
                    # With proxy authentication
                    auth, proxy_address = proxy_url.split("@")
                    login, password = auth.split(":")
                    proxy_host, proxy_port = proxy_address.split(":")
                else:
                    # Without proxy authentication
                    login, password = None, None
                    proxy_host, proxy_port = proxy_url.split(":")

                # Create a PySocks socket
                self.socket = socks.socksocket()
                self.socket.set_proxy(
                    proxy_type=socks.HTTP,
                    addr=proxy_host,
                    port=int(proxy_port),
                    username=login,
                    password=password,
                )
            except Exception as e:
                print(f"Error in proxy_http configuration: {e}")
                raise ValueError(
                    "Invalid proxy_http format. Expected 'http://[login:password@]host:port'"
                )
        else:
            # Without proxy
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Enable TLS if needed
        if self.tlsmode > 0:
            ctx = ssl.create_default_context()

            # Disable hostname and certificate verification
            if self.tlsmode > 1:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE

            self.socket = ctx.wrap_socket(self.socket, server_hostname=self.host)

        self.socket.connect((self.host, self.port))
        self._send(3, self.password)

    def disconnect(self):
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def _read(self, length):
        if platform.system() != "Windows":
            signal.alarm(self.timeout)
        data = b""
        while len(data) < length:
            data += self.socket.recv(length - len(data))
        if platform.system() != "Windows":
            signal.alarm(0)
        return data

    def _send(self, out_type, out_data):
        if self.socket is None:
            raise MCRconException("Must connect before sending data")

        # Send a request packet
        out_payload = (
            struct.pack("<ii", 0, out_type) + out_data.encode("utf8") + b"\x00\x00"
        )
        out_length = struct.pack("<i", len(out_payload))
        self.socket.send(out_length + out_payload)

        # Read response packets
        in_data = ""
        while True:
            # Read a packet
            (in_length,) = struct.unpack("<i", self._read(4))
            in_payload = self._read(in_length)
            in_id, in_type = struct.unpack("<ii", in_payload[:8])
            in_data_partial, in_padding = in_payload[8:-2], in_payload[-2:]

            # Sanity checks
            if in_padding != b"\x00\x00":
                raise MCRconException("Incorrect padding")
            if in_id == -1:
                raise MCRconException("Login failed")

            # Record the response
            in_data += in_data_partial.decode("utf8")

            # If there's nothing more to receive, return the response
            if len(select.select([self.socket], [], [], 0)[0]) == 0:
                return in_data

    def command(self, command):
        result = self._send(2, command)
        time.sleep(0.003)  # MC-72390 workaround
        return result
