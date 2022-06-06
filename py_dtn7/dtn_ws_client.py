import json
from urllib import request as rq
from typing import Optional, Any

import cbor2 as cbor
import rel
import websocket


def has_valid_schema(host: str):
    return host.startswith("wss://") or host.startswith("ws://")


def _rq_get(url: str) -> Any:
    return rq.urlopen(url=url)


class DTNWSClient:
    # base ws endpoint URL
    WS_BASE = "/ws"
    # returns the node id of the local instance
    NODE_ENDPOINT = "/node"
    # receive incoming bundles for this endpoint via the current websocket. NOTE: the endpoint must be already
    # registered to subscribe to it!
    SUBSCRIBE_ENDPOINT = "/subscribe"
    # stop receiving bundles for the given endpoint on this websocket connection. NOTE: They are still collected on the
    # node itself unless the endpoint is also unregistered!
    UNSUBSCRIBE_ENDPOINT = "/unsubscribe"
    # put this websocket into cbor data mode.
    DATA_MODE = "/data"
    # put this websocket into json mode.
    JSON_MODE = "/json"
    # put this websocket into raw bundle mode.
    BUNDLE_MODE = "/bundle"

    messages: list[str] = []

    def __init__(self, host: Optional[str] = None, port: Optional[str] = None):
        if port is None:
            port = 3000
        if host is None:
            host = "ws://localhost"

        if has_valid_schema(host):
            if host.endswith("/"):
                host = host[:-1]
            self._host = host
        else:
            raise ValueError("Host attribute must start either with 'ws://' or 'wss://'")

        self._port = port
        self._ws = websocket.WebSocketApp(f"{self._host}:{self._port}{self.WS_BASE}",
                                          on_open=self._on_open,
                                          on_message=self._on_message,
                                          on_error=self._on_error,
                                          on_close=self._on_close)
        #
        # self._nodeid = self.get_nodeid()
        self._ws.run_forever(dispatcher=rel)
        rel.signal(2, rel.abort)
        rel.dispatch()

    def get_nodeid(self) -> None:
        self._ws.send(data=self.NODE_ENDPOINT)

    def subscribe(self, endpoint: str):
        self._ws.send(data=f"{self.SUBSCRIBE_ENDPOINT} {endpoint}")

    def _on_open(self, ws: websocket.WebSocketApp):
        print("Connected")
        print(ws)
        self._ws.send(data=self.DATA_MODE)

    def _on_message(self, ws: websocket.WebSocketApp, msg):
        print(f"{msg=}")
        self.messages.append(msg)
        print(self.messages)

    def _on_error(self, ws: websocket.WebSocketApp, error):
        print(f"{error=}")

    def _on_close(self, status_code, msg):
        print(f"{status_code=}, {msg=}")
        print("Connection closed")

