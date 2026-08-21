# Algoritmo simples para inferir ligações:
# - hosts com mesmo MAC vendor + mesma interface -> provável ligada ao mesmo switch (inferred)
# - dispositivos que aparecem como gateway -> gateway (confirmed)
# - traceroute pode confirmar caminhos (quando disponível)
# Cada conexão terá 'confidence' = confirmed/probable/inferred/unknown e 'method' string.

def build_topology(devices, arp_entries, gateway_ip=None, traceroutes=None):
    nodes = []
    edges = []
    id_map = {}
    for idx, d in enumerate(devices, start=1):
        node = {
            "id": idx,
            "ip": d.get("ip"),
            "mac": d.get("mac"),
            "hostname": d.get("hostname") or d.get("ip"),
            "vendor": d.get("vendor"),
            "type": d.get("type", "unknown"),
            "last_seen": d.get("last_seen"),
        }
        id_map[d.get("ip")] = idx
        nodes.append(node)

    # Se houver gateway, conecte gateway -> switch/others como confirmed
    if gateway_ip and gateway_ip in id_map:
        gw_id = id_map[gateway_ip]
        for ip, nid in id_map.items():
            if ip == gateway_ip:
                continue
            edges.append({
                "source": gw_id,
                "target": nid,
                "confidence": "probable",
                "method": "route_inference"
            })

    # Use ARP/neigh to add probable links (infer)
    for a in arp_entries:
        ip = a.get("ip")
        mac = a.get("mac")
        if ip in id_map:
            # find other nodes sharing interface? simple inference: connect to gateway if known
            if gateway_ip and ip != gateway_ip and gateway_ip in id_map:
                edges.append({
                    "source": id_map[ip],
                    "target": id_map[gateway_ip],
                    "confidence": "inferred",
                    "method": "arp"
                })
    return {"nodes": nodes, "edges": edges}
