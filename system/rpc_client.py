"""Minimal MsgPack-RPC client for the Arduino Router on the Ventuno Q.

The router listens on a unix socket and routes calls to methods the MCU
sketch registered via Arduino_RouterBridge (Bridge.provide). We use this
instead of arduino-router-cli, whose response printer crashes on some
result types (observed: "panic: unsupported type: int8").

Protocol: request  [0, msgid, method, [args...]]
          response [1, msgid, error, result]   (error is None on success)
"""
import socket

import msgpack

SOCKET_PATH = "/var/run/arduino-router.sock"


class BridgeError(Exception):
    pass


class Bridge:
    def __init__(self, socket_path=SOCKET_PATH, timeout=15.0):
        self.socket_path = socket_path
        self.timeout = timeout
        self._msgid = 0

    def call(self, method, *args):
        self._msgid += 1
        msgid = self._msgid
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect(self.socket_path)
            sock.sendall(msgpack.packb([0, msgid, method, list(args)]))
            unpacker = msgpack.Unpacker(raw=False)
            while True:
                chunk = sock.recv(65536)
                if not chunk:
                    raise BridgeError(f"router closed connection on {method}")
                unpacker.feed(chunk)
                for response in unpacker:
                    _type, _id, error, result = response
                    if error is not None:
                        raise BridgeError(f"{method}: {error}")
                    return result
        finally:
            sock.close()
