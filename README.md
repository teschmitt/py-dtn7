# py-dtn7 (Work in Progress -- don't use yet)

[![Licence AGPL-3.0](https://img.shields.io/github/license/teschmitt/py-dtn7)](LICENSE)

A Python library for the DTN7 REST and WebSocket API of [dtn7-rs](https://github.com/dtn7/dtn7-rs)
including a BP7 style `Bundle` type (sort of).


### Be warned:

This is very much a work-in-progress.
Apart from not being very useful yet, anything might change at any time
since the package is still under development and the requirements are not all
completely clear yet.

### PR Politics

I'm sorry to say that right now I can't accept any Pull Requests, since this repo is part
of my Bachelor Thesis and logically any external contribution is forbidden. If you want to
contribute, please check back around November 2022. Until then feel free to
fork this repo and do some of your own experiments.

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

## Documentation

Use `pdoc` to generate the API docs or check out [py-dtn7.readthedocs.org](https://py-dtn7.readthedocs.org)
