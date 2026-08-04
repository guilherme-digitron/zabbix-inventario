from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from api.zabbix import get_hosts
from database.database import db
from database.models import HostOverride

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
