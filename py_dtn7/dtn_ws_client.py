import json
from base64 import b64encode
from enum import Enum
from typing import Any, Callable, ClassVar, Iterable, List, Optional, Union
from urllib import request as rq

import cbor2 as cbor
from websocket import ABNF, WebSocket, WebSocketApp

from py_dtn7 import Bundle


def _has_valid_schema(host: str):
    return host.startswith("wss://") or host.startswith("ws://")


def _rq_get(url: str) -> Any:
    return rq.urlopen(url=url)


class WSMode(Enum):
    DATA_MODE = 0
    JSON_MODE = 1


class DTNWSClient:
    """WebSocket Client connecting to a running dtnd instance"""

    # base ws endpoint URL
    _WS_BASE: ClassVar[str] = "/ws"
    # returns the node id of the local instance
    _NODE_ID_ENDPOINT: ClassVar[str] = "/node"
    # receive incoming bundles for this endpoint via the current websocket.
    # NOTE: the endpoint must be already registered to subscribe to it!
    _SUBSCRIBE_ENDPOINT: ClassVar[str] = "/subscribe"
    # stop receiving bundles for the given endpoint on this websocket connection.
    # NOTE: They are still collected on the node itself unless the endpoint is also unregistered!
    _UNSUBSCRIBE_ENDPOINT: ClassVar[str] = "/unsubscribe"
    # put this websocket into cbor data mode.
    _DATA_MODE: ClassVar[str] = "/data"
    # put this websocket into json mode.
    _JSON_MODE: ClassVar[str] = "/json"
    # put this websocket into raw bundle mode.
    _BUNDLE_MODE: ClassVar[str] = "/bundle"

    # instance attributes:
    _port: str
    _running: bool
    _callback: Union[Callable[[Bundle], Any], Callable[[str], Any]]
    _ws_base_url: str
    _endpoints: List[str]
    _mode: WSMode
    _ws: WebSocketApp

    def __init__(
        self,
        callback: Union[Callable[[Bundle], Any], Callable[[str], Any]],
        host: Optional[str] = None,
        port: Optional[str] = None,
        ws_base_url: Optional[str] = None,
        endpoints: Optional[Iterable[str]] = None,
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

        self._callback = callback
        self._port = port
        self._running = False
        self._ws_base_url = ws_base_url
        self._endpoints = endpoints
        self._mode = WSMode.DATA_MODE
        self._node_id = self._get_node_id()
        self._ws: WebSocketApp = WebSocketApp(
            f"{self._host}:{self._port}{self._ws_base_url}",
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )

    def start_client(self) -> None:
        """
        This will basically only call WebSocketApp.run_forever(). Since this blocks
        until the connection ends, dispatch this call to a separate thread in case
        there is code that should run afterwards.
        """
        self._ws.run_forever()

    def stop_client(self) -> None:
        if self._ws.keep_running:
            pass
        self._ws.close()

    @property
    def node_id(self) -> str:
        return self._node_id

    @property
    def mode(self) -> WSMode:
        return self._mode

    @mode.setter
    def mode(self, val: WSMode) -> None:
        if val == WSMode.DATA_MODE and self._mode != WSMode.DATA_MODE:
            self._ws.send(data=self._DATA_MODE)
        elif val == WSMode.JSON_MODE and self._mode != WSMode.JSON_MODE:
            self._ws.send(data=self._JSON_MODE)
        self._mode = val

    def send_data(
        self,
        destination: str,
        data: bytes,
        source: Optional[str] = None,
        delivery_notification: bool = False,
        lifetime: int = 24 * 3600 * 1000,
    ):
        if source is None:
            source = self._node_id

        bundle_dict: dict = {
            "src": source,
            "dst": destination,
            "delivery_notification": delivery_notification,
            "lifetime": lifetime,
            "data": data,
        }

        payload: bytes
        if self._mode == WSMode.DATA_MODE:
            payload = cbor.dumps(bundle_dict)
        else:
            try:
                # encode in base64 and translate to str equivalent according to spec:
                # https://github.com/dtn7/dtn7-rs/blob/9b166/doc/http-client-api.md
                bundle_dict["data"] = b64encode(bundle_dict["data"]).decode("utf-8")
            except TypeError as e:
                raise TypeError(f"Argument data must be of type 'bytes': {e}")
            json_str = json.dumps(bundle_dict)
            payload = json_str.encode()
        self._ws.send(payload, opcode=ABNF.OPCODE_BINARY)

    def subscribe(self, endpoint: str):
        self._ws.send(data=f"{self._SUBSCRIBE_ENDPOINT} {endpoint}")

    def _on_open(self, ws: WebSocketApp) -> None:
        self._ws.send(data=self._DATA_MODE)
        for eid in self._endpoints:
            ws.send(data=f"{self._SUBSCRIBE_ENDPOINT} {eid}")
        self._running = True

    def _on_message(self, ws: WebSocketApp, msg: Any) -> None:
        # print(f"{msg}")
        # _log(msg)
        # self.messages.append(msg)
        self._callback(msg)

    def _on_error(self, ws: WebSocketApp, error) -> None:
        print(f"{error}")

    def _on_close(self, ws: WebSocketApp, status_code, msg) -> None:
        # print(f"{status_code}, {msg}")
        self._running = False
        print("Connection closed")

    def _get_node_id(self) -> str:
        short_ws: WebSocket = WebSocket()
        short_ws.connect(
            url=f"{self._host}:{self._port}{self._ws_base_url}",
        )
        short_ws.send(self._NODE_ID_ENDPOINT)
        resp: str = short_ws.recv()
        if not resp.startswith("200 node:"):
            raise RuntimeError("Node ID could not be determined.")
        short_ws.close()
        return resp.split(":", maxsplit=1)[1].strip()

    @property
    def running(self) -> bool:
        return self._running
