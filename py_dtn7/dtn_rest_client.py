import json
from typing import ClassVar, Optional, Union, List

import requests as rq
from requests import Response

from py_dtn7 import Bundle


def has_valid_schema(host: str):
    return host.startswith("https://") or host.startswith("http://")


class DTNRESTClient:
    # API endpoints
    DOWNLOAD_ENDPOINT: ClassVar[str] = "/download"
    ENDPOINT_ENDPOINT: ClassVar[str] = "/endpoint"
    REGISTER_ENDPOINT: ClassVar[str] = "/register"
    SEND_ENDPOINT: ClassVar[str] = "/send"
    UNREGISTER_ENDPOINT: ClassVar[str] = "/unregister"
    STATUS_BUNDLES: ClassVar[str] = "/status/bundles"
    STATUS_FILTER_BUNDLES: ClassVar[str] = "/status/bundles/filtered"
    STATUS_EIDS: ClassVar[str] = "/status/eids"
    STATUS_INFO: ClassVar[str] = "/status/info"
    STATUS_NODEID: ClassVar[str] = "/status/nodeid"
    STATUS_PEERS: ClassVar[str] = "/status/peers"
    STATUS_STORE: ClassVar[str] = "/status/store"

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        if port is None:
            port = 3000
        if host is None:
            host = "http://localhost"

        if has_valid_schema(host):
            if host.endswith("/"):
                host = host[:-1]
            self._host = host
        else:
            raise ValueError("Host attribute must start either with 'http://' or 'https://'")

        self._port = port
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

    def get_all_bundles(self) -> List[Bundle]:
        """
        Gets all bundles as Bundle objects from the DTNd store. This can cause very much traffic
        so be sure to use with care.
        :return: all Bundles that are in the DTNd store
        """
        return [
            Bundle.from_cbor(bundle.content)
            for bundle in [
                rq.get(url=f"{self._host}:{self._port}{self.DOWNLOAD_ENDPOINT}?{burl}")
                for burl in self._raw_bundles
            ]
        ]

    def get_filtered_bundles(self, address_part_criteria: str):
        """

        :param address_part_criteria:
        :return:
        """
        bundles: List[str] = json.loads(
            rq.get(
                url=(
                    f"{self._host}:{self._port}{self.STATUS_FILTER_BUNDLES}"
                    f"?addr={address_part_criteria}"
                )
            ).content
        )
        return [
            Bundle.from_cbor(bundle.content)
            for bundle in [
                rq.get(url=f"{self._host}:{self._port}{self.DOWNLOAD_ENDPOINT}?{burl}")
                for burl in bundles
            ]
        ]

    def fetch_endpoint(self, endpoint: str = None) -> bytes:
        if endpoint is None:
            endpoint = self._nodeid
        return rq.get(url=f"{self._host}:{self._port}{self.ENDPOINT_ENDPOINT}?{endpoint}").content

    def download(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        bundle_id: Optional[str] = None,
        node_id: Optional[str] = None,
        peer_name: Optional[str] = None,
        time: Optional[int] = None,
        seq: Optional[int] = None,
    ) -> bytes:
        if bundle_id is None:
            if time is None or seq is None:
                raise ValueError(
                    "In absence of a bundle_id, time and sequence number must be provided."
                )
            if node_id is None:
                if peer_name is None:
                    node_id = self._nodeid
                else:
                    peers = self.peers
                    if peer_name in peers.keys():
                        node_id = f"dtn:{peers[peer_name]['eid'][1]}"
                    else:
                        raise ValueError("Peer not found")
            else:
                if node_id[-1] != "/":
                    node_id = f"{node_id}/"
            bundle_id = f"{node_id}-{time}-{seq}"

        if host is None:
            if port is None:
                host = self._host
                port = self._port
            else:
                raise ValueError("Host and port must either both be defined or undefined.")
        else:
            if not has_valid_schema(host):
                raise ValueError("Host attribute must start either with 'http://' or 'https://'")
            if host[-1] == "/":
                host = host[:-1]

        return rq.get(url=f"{host}:{port}{self.DOWNLOAD_ENDPOINT}?{bundle_id}").content

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @property
    def endpoints(self) -> list:
        eps: list = json.loads(rq.get(url=f"{self._host}:{self._port}{self.STATUS_EIDS}").content)
        # eps = list(map(lambda ep: ep.rsplit("/", 1)[1], eps))
        return eps

    @property
    def bundles(self) -> List[dict]:
        res: list = []
        for bundle in self._raw_bundles:
            nodeid, dtn_time, seq_nr = bundle.rsplit("-", 2)
            res.append({"node_id": nodeid, "time": int(dtn_time), "seq": int(seq_nr)})
        return res

    @property
    def _raw_bundles(self) -> List[str]:
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
