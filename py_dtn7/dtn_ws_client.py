import json
from enum import Enum
from urllib import request as rq
from typing import Optional, Any, Callable, ClassVar

import cbor2 as cbor
from websocket import WebSocketApp

from py_dtn7 import Bundle


def _has_valid_schema(host: str):
    return host.startswith("wss://") or host.startswith("ws://")


def _rq_get(url: str) -> Any:
    return rq.urlopen(url=url)


def _log(msg: str) -> None:
    with open("msgs.log", "a+") as f:
        f.write(f"{msg}\n")


class ModeEnum(Enum):
    DATA_MODE = "Data Mode"
    JSON_MODE = "JSON Mode"


class DTNWSClient:
    """ WebSocket Client connecting to a running dtnd instance"""

    # base ws endpoint URL
    _WS_BASE: ClassVar[str] = "/ws"
    # returns the node id of the local instance
    _NODE_ENDPOINT: ClassVar[str] = "/node"
    # receive incoming bundles for this endpoint via the current websocket. NOTE: the endpoint must be already
    # registered to subscribe to it!
    _SUBSCRIBE_ENDPOINT: ClassVar[str] = "/subscribe"
    # stop receiving bundles for the given endpoint on this websocket connection. NOTE: They are still collected on the
    # node itself unless the endpoint is also unregistered!
    _UNSUBSCRIBE_ENDPOINT: ClassVar[str] = "/unsubscribe"
    # put this websocket into cbor data mode.
    _DATA_MODE: ClassVar[str] = "/data"
    # put this websocket into json mode.
    _JSON_MODE: ClassVar[str] = "/json"
    # put this websocket into raw bundle mode.
    _BUNDLE_MODE: ClassVar[str] = "/bundle"

    # instance attributes:
    _port: str
    _callback: Callable[[Bundle | str], Any]
    _ws_base_url: str
    _endpoints: list[str]
    _mode: ModeEnum
    _ws: WebSocketApp

    def __init__(
        self,
        callback: Callable[[Bundle | str], Any],
        host: Optional[str] = None,
        port: Optional[str] = None,
        ws_base_url: Optional[str] = None,
        endpoints: Optional[list[str]] = None
    ):
        """

        :param callback: method to call when data is received
        :param host: host of DTN7 daemon
        :param port: port of DTN7 daemon
        """
        if port is None:
            port = 3000
        if host is None:
            host = "ws://localhost"
        if ws_base_url is None:
            ws_base_url = self._WS_BASE
        if endpoints is None:
            endpoints = []

        if _has_valid_schema(host):
            if host.endswith("/"):
                host = host[:-1]
            self._host = host
        else:
            raise ValueError("Host attribute must start either with 'ws://' or 'wss://'")

        self._callback: Callable[[Bundle | str], Any] = callback
        self._port: str = port
        self._ws_base_url: str = ws_base_url
        self._endpoints: list[str] = endpoints
        self._mode: ModeEnum = ModeEnum.DATA_MODE
        self._ws: WebSocketApp  = WebSocketApp(
            f"{self._host}:{self._port}{self._ws_base_url}",
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

    def start_client(self):
        self._ws.run_forever()

    def stop_client(self) -> None:
        if self._ws.keep_running:
            pass
        self._ws.close()

    def node_id(self) -> None:
        self._ws.send(data=self._NODE_ENDPOINT)

    @property
    def mode(self) -> ModeEnum:
        return self._mode

    def subscribe(self, endpoint: str):
        _log(f"SUBSCRIBE command received: {self._SUBSCRIBE_ENDPOINT} {endpoint}")
        self._ws.send(data=f"{self._SUBSCRIBE_ENDPOINT} {endpoint}")

    def _on_open(self, ws: WebSocketApp) -> None:
        print("Connected")
        print(ws)
        self._ws.send(data=self._JSON_MODE)
        for eid in self._endpoints:
            ws.send(data=f"{self._SUBSCRIBE_ENDPOINT} {eid}")

    def _on_message(self, ws: WebSocketApp, msg: Any) -> None:
        # print(f"{msg=}")
        # _log(msg)
        # self.messages.append(msg)
        self._callback(msg)

    def _on_error(self, ws: WebSocketApp, error) -> None:
        print(f"{error=}")

    def _on_close(self, ws: WebSocketApp, status_code, msg) -> None:
        print(f"{status_code=}, {msg=}")
        print("Connection closed")
