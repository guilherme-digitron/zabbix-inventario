import requests

from config import ZABBIX_URL,TOKEN

headers={
"Content-Type":"application/json-rpc"
}

def call(method,params):

    payload={
        "jsonrpc":"2.0",
        "method":method,
        "params":params,
        "id":1
    }

    headers={
        "Authorization":"Bearer "+TOKEN,
        "Content-Type":"application/json-rpc"
    }

    r=requests.post(
        ZABBIX_URL,
        json=payload,
        headers=headers,
        verify=False
    )

    return r.json()["result"]

def get_hosts():
    # inclui hostid para referência e busca
    return call(
        "host.get",
        {
            "output": [
                "hostid",
                "host",
                "name",
                "status",
                "available"
            ],
            "selectInterfaces": [
                "ip"
            ],
            "selectInventory": "extend"
        }
    )

def list_items(hostid):

    return call(
        "item.get",
        {
            "hostids": hostid,
            "output": [
                "name",
                "key_",
                "lastvalue"
            ]
        }
    )
