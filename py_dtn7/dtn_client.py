import json
from typing import Optional, Union

import cbor2 as cbor
import requests as rq
from requests import Response
from requests.exceptions import InvalidSchema


class DTNClient:

    # API endpoints
    DOWNLOAD_ENDPOINT = "/download"
    REGISTER_ENDPOINT = "/register"
    SEND_ENDPOINT = "/send"
    UNREGISTER_ENDPOINT = "/unregister"
    STATUS_BUNDLES = "/status/bundles"
    STATUS_EIDS = "/status/eids"
    STATUS_INFO = "/status/info"
    STATUS_NODEID = "/status/nodeid"
    STATUS_PEERS = "/status/peers"
    STATUS_STORE = "/status/store"

    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        endpoints: Optional[list[str]] = None,
    ):
        if port is None:
            port = 3000

        if host.startswith("https://") or host.startswith("http://"):
            self._host = host
        else:
            raise InvalidSchema("Host attribute must start either with 'http://' or 'https://'")

        self._port = port
        self._endpoints = endpoints if endpoints is not None else []

        self._nodeid = self._get_nodeid()

    def send(
        self,
        payload: Union[bytes, dict, str],
        destination: Optional[str] = None,
        peer_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        lifetime: Optional[int] = None,
        encoding: Optional[str] = None,
    ) -> Response:

        dst: str = ""

        if destination is not None:
            dst = destination
        elif peer_name is not None and endpoint is not None:
            peers = self.peers
            if peer_name in peers.keys():
                dst = f"dtn:{peers[peer_name]['eid'][1]}{endpoint}"
            else:
                known_peers: str = ", ".join([k for k in peers.keys()])
                raise ValueError(f"Unknown peer name passed. Known peers: {known_peers}")
        url: str = f"{self._host}:{self._port}{self.SEND_ENDPOINT}?dst={dst}"
        if lifetime is not None:
            url += f"&lifetime={lifetime}"
        if type(payload) is str:
            if encoding is None:
                encoding = "utf-8"
            response: Response = rq.post(url=url, data=payload.encode(encoding=encoding))
        elif type(payload) is dict:
            response: Response = rq.post(url=url, json=payload)
        elif type(payload) is bytes:
            response: Response = rq.post(url=url, data=payload)
        else:
            raise ValueError("Payload must by of type 'bytes', 'dict' or 'str'.")

        return response

    def register(self, endpoint: str) -> Response:
        response: Response = rq.get(
            url=f"{self._host}:{self._port}{self.REGISTER_ENDPOINT}?{endpoint}"
        )
        result: str = response.content.decode("utf-8").lower()
        if "registered" not in result or endpoint not in result:
            raise RuntimeError(f'Something went wrong, endpoint "{endpoint}" not registered')
        return response

    def unregister(self, endpoint: str) -> Response:
        response: Response = rq.get(
            url=f"{self._host}:{self._port}{self.UNREGISTER_ENDPOINT}?{endpoint}"
        )
        result: str = response.content.decode("utf-8").lower()
        if "unregistered" not in result or endpoint not in result:
            raise RuntimeError(f'Something went wrong, endpoint "{endpoint}" not unregistered')
        return response

    def get_all_bundles(self) -> list:
        return [
            cbor.loads(bundle.content)
            for bundle in [
                rq.get(url=f"{self._host}:{self._port}{self.DOWNLOAD_ENDPOINT}?{burl}")
                for burl in self._raw_bundles
            ]
        ]

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def endpoints(self) -> list:
        return json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_EIDS}").content)

    @property
    def bundles(self) -> list[dict]:
        res: list = []
        for bundle in self._raw_bundles:
            nodeid, dtn_time, seq_nr = bundle.rsplit("-", 2)
            res.append({"node_id": nodeid, "time": int(dtn_time), "seq": int(seq_nr)})
        return res

    @property
    def _raw_bundles(self) -> list[str]:
        return json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_BUNDLES}").content)

    @property
    def store(self) -> list:
        return json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_STORE}").content)

    @property
    def info(self) -> dict:
        return json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_INFO}").content)

    @property
    def peers(self) -> dict:
        return json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_PEERS}").content)

    @property
    def node_id(self) -> str:
        return self._nodeid

    def __str__(self):
        return self.__repl__()

    def __repl__(self):
        return f"<DTNClient@{self._host}:{self._port}, node ID: {self._nodeid}>"

    def _get_nodeid(self) -> Optional[str]:
        return rq.get(url=f"{self._host}:{self._port}{self.STATUS_NODEID}").content.decode("utf-8")
