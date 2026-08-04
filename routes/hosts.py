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

@hosts.route("/all")
def all_hosts():
    q = request.args.get("q", "").strip()
    hosts = get_hosts()
    results = []
    for h in hosts:
        hostname = h.get("host", "")
        # filtra por hostname se query foi passada
        if q and q.lower() not in hostname.lower():
            continue
        # IP extraction: mais defensivo
        interfaces = h.get("interfaces") or []
        ip = None
        if interfaces:
            for iface in interfaces:
                if iface and iface.get("ip"):
                    ip = iface.get("ip")
                    break
        inventory = h.get("inventory") or {}
        mac = inventory.get("macaddress_a") or inventory.get("macaddress") or inventory.get("mac")
        serial = inventory.get("serialno_a") or inventory.get("serialno") or inventory.get("serial")
        model = inventory.get("model")
        override = HostOverride.query.filter_by(zabbix_hostid=str(h.get("hostid"))).first()
        merged = {
            "hostid": h.get("hostid"),
            "host": hostname,
            "ip": ip,
            "mac": mac,
            "serial": serial,
            "model": model,
            "available": h.get("available"),
            "override_username": override.username if override else None,
            "override_anydesk": override.anydesk if override else None,
            "raw_inventory": inventory
        }
        results.append(merged)
    return render_template("all.html", hosts=results, q=q)

@hosts.route("/all/export", methods=["POST"])
def export_all():
    q = request.form.get("q", "").strip()
    hosts = get_hosts()
    results = []
    # prepare merged hosts same as /all
    for h in hosts:
        hostname = h.get("host", "")
        if q and q.lower() not in hostname.lower():
            continue
        interfaces = h.get("interfaces") or []
        ip = None
        if interfaces:
            for iface in interfaces:
                if iface and iface.get("ip"):
                    ip = iface.get("ip")
                    break
        inventory = h.get("inventory") or {}
        mac = inventory.get("macaddress_a") or inventory.get("macaddress") or inventory.get("mac")
        serial = inventory.get("serialno_a") or inventory.get("serialno") or inventory.get("serial")
        model = inventory.get("model")
        override = HostOverride.query.filter_by(zabbix_hostid=str(h.get("hostid"))).first()
        merged = {
            "hostid": h.get("hostid"),
            "host": hostname,
            "ip": ip,
            "mac": mac,
            "serial": serial,
            "model": model,
            "available": h.get("available"),
            "override_username": override.username if override else None,
            "override_anydesk": override.anydesk if override else None
        }
        results.append(merged)
    # collect item names across hosts
    all_item_names = set()
    host_items_map = {}
    for h in results:
        hid = h["hostid"]
        items = []
        try:
            items = list_items(hid) or []
        except Exception as e:
            current_app.logger.exception(f"Error fetching items for host {hid}: {e}")
            items = []
        item_map = {it.get("name"): it.get("lastvalue") for it in items}
        host_items_map[hid] = item_map
        all_item_names.update(item_map.keys())
    # prepare CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"inventory_{timestamp}.csv"
    exports_dir = os.path.join(current_app.root_path, "exports")
    os.makedirs(exports_dir, exist_ok=True)
    filepath = os.path.join(exports_dir, filename)
    base_headers = ["hostid","Hostname","IP","MAC","Serial","Model","Available","Username","Anydesk"]
    item_headers = sorted(all_item_names)
    headers = base_headers + item_headers
    try:
        with open(filepath, "w", newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for h in results:
                hid = h["hostid"]
                row = [hid, h.get("host"), h.get("ip"), h.get("mac"), h.get("serial"), h.get("model"), h.get("available"), h.get("override_username"), h.get("override_anydesk")]
                item_map = host_items_map.get(hid, {})
                for name in item_headers:
                    row.append(item_map.get(name, ""))
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
    # safety: prevent directory traversal
    safe_name = os.path.basename(filename)
    exports_dir = os.path.join(current_app.root_path, "exports")
    path = os.path.join(exports_dir, safe_name)
    if not os.path.exists(path):
        flash("Arquivo não encontrado", "danger")
        return redirect(url_for('hosts.exports_list'))
    # render CSV as HTML table
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
    # preferência: pegamos hostid do path, mas caímos para o form se faltar
    form_hostid = request.form.get("hostid") or hostid
    username = request.form.get("username", "").strip()
    anydesk = request.form.get("anydesk", "").strip()
    hostname = request.form.get("hostname", "")
    ip = request.form.get("ip", "")
    mac = request.form.get("mac", "")
    # log para debug
    current_app.logger.info(f"Update host: hostid(path)={hostid} hostid(form)={form_hostid} username={username} anydesk={anydesk}")
    # persistir
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
