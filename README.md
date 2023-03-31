# py-dtn7 (Work in Progress -- don't use yet)

[![Licence AGPL-3.0](https://img.shields.io/github/license/teschmitt/py-dtn7)](LICENSE)

A Python wrapper library for the DTN7 REST and WebSocket API of [dtn7-rs](https://github.com/dtn7/dtn7-rs).
The library includes a fully spec compliant `Bundle` type (but without fragment and CRC support), which allows full
bundle creation and (de-)serialization.

The `bundle.py`, `dtn_rest_client.py`, `utils.py` modules/files are Micropython compatible.
But, this requires a bit of manual library management.
Please refer to the Micropython installation guide below.

### Getting Started

To use `py-dtn7` in your project, simply install it from PyPI with Poetry:

```shell
$ poetry install --no-dev py_dtn7
```

### Development

This is very much a work-in-progress and by far not complete. The Bundle
implementation is very rudimentary and does not support any blocks other
than Primary and Payload.

To generate the API documentation use `pdoc`:

```shell
$ pdoc ./py_dtn7 --output-directory ./docs
```

... or check out [py-dtn7.readthedocs.org](https://py-dtn7.readthedocs.org)


## Quickstart

```pycon
>>> from py_dtn7 import DTNRESTClient
>>> client = DTNRESTClient(host="http://localhost", port=3000)
>>> d.peers
{'box1': {'eid': [1, '//box1/'], 'addr': {'Ip': '10.0.0.42'}, 'con_type': 'Dynamic', 'period': None, 'cla_list': [['MtcpConvergenceLayer', 16162]], 'services': {}, 'last_contact': 1653316457}}
>>> d.info
{'incoming': 0, 'dups': 0, 'outgoing': 0, 'delivered': 3, 'broken': 0}
```

When sending a bundle to a known peer, we can simply supply the peer name and endpoint,
otherwise we use the complete URI:

```pycon
>>> d.send(payload={"body": "This will be transferred as json"}, peer_name="box1", endpoint="info")
<Response [200]>
>>> r = d.send(payload="Is there anybody out there?", destination="dtn://greatunkown/incoming")
>>> r.content.decode("utf-8")
'Sent payload with 27 bytes'
```

## Micropython Installation Guide

To be extended:

The dummy libraries `__future__.py`, `abc.py`, `typing.py`, the [micropython-cbor](https://github.com/alexmrqt/micropython-cbor/) library (specifically the `cbor.py` module/file) and `urequests` as well as `datetime` are needed:

```shell
$ mpremote mip install urequests
$ mpremote mip install datetime
```
