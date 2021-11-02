from pathlib import Path
import json
from pprint import pprint
import os
import base64
from time import sleep
from datetime import datetime, timedelta

# Pip installed Modules
from lndgrpc import LNDClient
from lndgrpc.client import ln
from protobuf_to_dict import protobuf_to_dict

credential_path = os.getenv("LND_CRED_PATH", None)
if credential_path == None:
	credential_path = Path.home().joinpath(".lnd")
	mac = str(credential_path.joinpath("data/chain/bitcoin/mainnet/admin.macaroon").absolute())
else:
	credential_path = Path(credential_path)
	mac = str(credential_path.joinpath("admin.macaroon").absolute())
	

node_ip = os.getenv("LND_NODE_IP")
node_port = os.getenv("LND_NODE_PORT")
tls = str(credential_path.joinpath("tls.cert").absolute())

lnd_ip_port = f"{node_ip}:{node_port}"

lnd = LNDClient(
	lnd_ip_port,
	macaroon_filepath=mac,
	cert_filepath=tls
	# no_tls=True
)

mypk = lnd.get_info().identity_pubkey

# from is a python keyword, so we gotta do something fancy here with kwargs
kwargs = {}
kwargs["from"] = bytes.fromhex("03bec0f5799c4ae2d0fa8943f089324bddd6cbbbb6178f7ac2f2588696280e6587")
kwargs["to"] = bytes.fromhex("02ad6fb8d693dc1e4569bcedefadf5f72a931ae027dc0f0c544b34c1c6f3b9a02b")
ignored = [
    ln.NodePair(**kwargs),
]

kwargs = {}
kwargs["from"] = bytes.fromhex("03bec0f5799c4ae2d0fa8943f089324bddd6cbbbb6178f7ac2f2588696280e6587")
kwargs["to"] = bytes.fromhex("037659a0ac8eb3b8d0a720114efc861d3a940382dcfa1403746b4f8f6b2e8810ba")
ignored.append(ln.NodePair(**kwargs))

fee_limit = ln.FeeLimit(fixed=11)

dest_pk = "0219426a5b641ed05ee639bfda80c1e0199182944977686d1dd1ea2dcb89e5dd55"


for i in range(10,1000,5):
    fee_limit = ln.FeeLimit(fixed=i)
    # Circular rebalance
    r = lnd.query_routes(
        pub_key=mypk,
        amt=100000,
        final_cltv_delta=40,
        fee_limit=fee_limit,
        # ignored_nodes=,
        # source_pub_key=,
        ignored_pairs=ignored,
        cltv_limit=144,
        outgoing_chan_id=695801744448487425,
        last_hop_pubkey=bytes.fromhex("03f9dc7982e336c1d4115459d59f40589db9db1a70adf741ed96584b79f60612cb"),
    )
    try:
        print(r.routes[0].total_fees)
        break
    except AttributeError:
        pass



from hashlib import sha256
import secrets
preimageByteLength = 32
preimage = secrets.token_bytes(preimageByteLength)
m = sha256()
m.update(preimage)
preimage_hash = m.digest()

inv = lnd.add_invoice(100000,"rebalance test")
pr = lnd.decode_pay_req(inv.payment_request)
route = r.routes[0]
route.hops[-1].mpp_record.total_amt_msat = pr.num_msat
route.hops[-1].mpp_record.payment_addr = pr.payment_addr
lnd.send_to_route(
    pay_hash = bytes.fromhex(pr.payment_hash),
    route=route
)

# ln.list_channels().query("chan_id == 762928028804382736 | remote_pubkey == '037659a0ac8eb3b8d0a720114efc861d3a940382dcfa1403746b4f8f6b2e8810ba'")