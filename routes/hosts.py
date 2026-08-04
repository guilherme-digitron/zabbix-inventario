from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from api.zabbix import get_hosts, list_items
from database.database import db
from database.models import HostOverride
import os
import csv
from datetime import datetime

hosts = Blueprint("hosts", __name__)

@hosts.route("/hosts")
def list_hosts():
    data = get_hosts()
    return render_template("hosts.html", hosts=data)

@hosts.route("/teste")
def teste():
    # Página para testes antes de produção
    hosts = get_hosts()
    # mostra dados brutos para debug
    return render_template("teste.html", hosts=hosts)

def extract_items_for_host(hostid):
    """Return a dict with keys we care about for the inventory for this host."""
    items = []
    try:
        items = list_items(hostid) or []
    except Exception as e:
        current_app.logger.exception(f"Error fetching items for host {hostid}: {e}")
        items = []
    item_map = {}
    for it in items:
        key = it.get("key_") or ""
        name = (it.get("name") or "").lower()
        last = it.get("lastvalue")
        item_map[key] = last
        item_map[name] = last
    return item_map

@hosts.route("/all")
def all_hosts():
    q = request.args.get("q", "").strip()
    raw_hosts = get_hosts()
    results = []
    for h in raw_hosts:
        hostname = h.get("host", "")
        if q and q.lower() not in hostname.lower():
            continue
        hostid = h.get("hostid")
        # extract IP defensively
        interfaces = h.get("interfaces") or []
        ip = ""
        if interfaces:
            for iface in interfaces:
                if iface and iface.get("ip"):
                    ip = iface.get("ip")
                    break
        inventory = h.get("inventory") or {}
        serial = inventory.get("serialno_a") or inventory.get("serialno") or inventory.get("serial")
        model = inventory.get("model")
        # fetch items for specific keys
        item_map = extract_items_for_host(hostid)
        agente_val = None
        # agent.ping may present as key 'agent.ping' or name containing 'agente'
        if 'agent.ping' in item_map:
            agente_val = item_map.get('agent.ping')
        else:
            # try name-based
            for k in item_map:
                if 'agente' in k or 'agent' in k:
                    agente_val = item_map.get(k)
                    break
        # macs: try system.hw.macaddr or names containing 'mac'
        mac_val = None
        for k in item_map:
            if k.startswith('system.hw.macaddr') or 'mac' in k:
                mac_val = item_map.get(k)
                break
        # net.if.list and net.if.discovery
        net_if_list = None
        net_if_disc = None
        for k in item_map:
            if 'net.if.list' in k or 'net.if.list' in str(k):
                net_if_list = item_map.get(k)
            if 'net.if.discovery' in k or 'net.if.discovery' in str(k):
                net_if_disc = item_map.get(k)
        merged = {
            "hostid": hostid,
            "host": hostname,
            "ip": ip,
            "mac": mac_val,
            "serial": serial,
            "model": model,
            "available": h.get("available"),
            "agente": agente_val,
            "net_if_list": net_if_list,
            "net_if_disc": net_if_disc,
            "raw_inventory": inventory,
            "item_map": item_map,
        }
        results.append(merged)
    return render_template("all.html", hosts=results, q=q)

@hosts.route("/all/export", methods=["POST"])  # kept for compatibility
@hosts.route("/export", methods=["POST"])      # new route so dashboard can post here
def export_all():
    q = request.form.get("q", "").strip()
    raw_hosts = get_hosts()
    results = []
    for h in raw_hosts:
        hostname = h.get("host", "")
        if q and q.lower() not in hostname.lower():
            continue
        hostid = h.get("hostid")
        interfaces = h.get("interfaces") or []
        ip = ""
        if interfaces:
            for iface in interfaces:
                if iface and iface.get("ip"):
                    ip = iface.get("ip")
                    break
        inventory = h.get("inventory") or {}
        serial = inventory.get("serialno_a") or inventory.get("serialno") or inventory.get("serial")
        model = inventory.get("model")
        item_map = extract_items_for_host(hostid)
        agente_val = item_map.get('agent.ping') or item_map.get('agente') or item_map.get('agent')
        mac_val = None
        for k in item_map:
            if k.startswith('system.hw.macaddr') or 'mac' in k:
                mac_val = item_map.get(k)
                break
        net_if_list = None
        net_if_disc = None
        for k in item_map:
            if 'net.if.list' in k:
                net_if_list = item_map.get(k)
            if 'net.if.discovery' in k:
                net_if_disc = item_map.get(k)
        merged = {
            "hostid": hostid,
            "host": hostname,
            "ip": ip,
            "mac": mac_val,
            "serial": serial,
            "model": model,
            "available": h.get("available"),
            "agente": agente_val,
            "net_if_list": net_if_list,
            "net_if_disc": net_if_disc,
            "item_map": item_map,
        }
        results.append(merged)
    # prepare CSV only with requested columns
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_{timestamp}.csv"
    exports_dir = os.path.join(current_app.root_path, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    filepath = os.path.join(exports_dir, filename)
    headers = ["hostid","Hostname","IP","MAC","Serial","Model","Agente","NetIfList","NetIfDiscovery","Available"]
    try:
        with open(filepath, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for h in results:
                agente_display = 'Online' if str(h.get('agente') or '').strip() == '1' or str(h.get('agente') or '').strip().lower() == '1' else 'Offline'
                row = [h.get('hostid'), h.get('host'), h.get('ip'), h.get('mac') or '', h.get('serial') or '', h.get('model') or '', agente_display, h.get('net_if_list') or '', h.get('net_if_disc') or '', h.get('available')]
                writer.writerow(row)
        flash(f"Export criado: {filename}", "success")
    except Exception as e:
        current_app.logger.exception(f"Failed to write export {filepath}: {e}")
        flash("Falha ao criar export: " + str(e), "danger")
    return redirect(url_for("hosts.exports_list"))

@hosts.route("/exports")
def exports_list():
    exports_dir = os.path.join(current_app.root_path, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    files = []
    for name in os.listdir(exports_dir):
        path = os.path.join(exports_dir, name)
        if os.path.isfile(path) and name.endswith('.csv'):
            mtime = os.path.getmtime(path)
            files.append({"name": name, "mtime": mtime})
    files_sorted = sorted(files, key=lambda x: x['mtime'], reverse=True)
    return render_template("exports.html", files=files_sorted)

@hosts.route("/exports/view/<path:filename>")
def exports_view(filename):
    safe_name = os.path.basename(filename)
    exports_dir = os.path.join(current_app.root_path, "exports")
    path = os.path.join(exports_dir, safe_name)
    if not os.path.exists(path):
        flash("Arquivo não encontrado", "danger")
        return redirect(url_for('hosts.exports_list'))
    rows = []
    try:
        with open(path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for r in reader:
                rows.append(r)
    except Exception as e:
        current_app.logger.exception(f"Failed reading export {path}: {e}")
        flash("Falha ao ler arquivo: " + str(e), "danger")
        return redirect(url_for('hosts.exports_list'))
    return render_template('export_view.html', filename=safe_name, rows=rows)

@hosts.route("/exports/download/<path:filename>")
def exports_download(filename):
    safe_name = os.path.basename(filename)
    exports_dir = os.path.join(current_app.root_path, "exports")
    if not os.path.exists(os.path.join(exports_dir, safe_name)):
        flash("Arquivo não encontrado", "danger")
        return redirect(url_for('hosts.exports_list'))
    return send_from_directory(exports_dir, safe_name, as_attachment=True)

@hosts.route("/hosts/<hostid>/update", methods=["POST"])
def update_host(hostid):
    form_hostid = request.form.get("hostid") or hostid
    username = request.form.get("username", "").strip()
    anydesk = request.form.get("anydesk", "").strip()
    hostname = request.form.get("hostname", "")
    ip = request.form.get("ip", "")
    mac = request.form.get("mac", "")
    current_app.logger.info(f"Update host: hostid(path)={hostid} hostid(form)={form_hostid} username={username} anydesk={anydesk}")
    override = HostOverride.query.filter_by(zabbix_hostid=str(form_hostid)).first()
    if not override:
        override = HostOverride(zabbix_hostid=str(form_hostid))
        db.session.add(override)
    override.username = username or None
    override.anydesk = anydesk or None
    override.hostname = hostname or None
    override.ip = ip or None
    override.mac = mac or None
    db.session.commit()
    flash("Dados salvos para host {}".format(hostname or form_hostid), "success")
    return redirect(url_for("hosts.all_hosts"))
