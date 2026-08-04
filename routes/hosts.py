from flask import Blueprint, render_template, request, redirect, url_for, flash
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
        override = HostOverride.query.filter_by(zabbix_hostid=str(h.get("hostid"))).first()
        merged = {
            "hostid": h.get("hostid"),
            "host": hostname,
            "ip": (h.get("interfaces") or [{}])[0].get("ip"),
            "mac": h.get("inventory", {}).get("macaddress_a"),
            "serial": h.get("inventory", {}).get("serialno_a"),
            "model": h.get("inventory", {}).get("model"),
            "available": h.get("available"),
            "override_username": override.username if override else None,
            "override_anydesk": override.anydesk if override else None,
            "raw_inventory": h.get("inventory")
        }
        results.append(merged)
    return render_template("all.html", hosts=results, q=q)

@hosts.route("/hosts/<hostid>/update", methods=["POST"])
def update_host(hostid):
    username = request.form.get("username", "").strip()
    anydesk = request.form.get("anydesk", "").strip()
    hostname = request.form.get("hostname", "")
    ip = request.form.get("ip", "")
    mac = request.form.get("mac", "")
    override = HostOverride.query.filter_by(zabbix_hostid=str(hostid)).first()
    if not override:
        override = HostOverride(zabbix_hostid=str(hostid))
        db.session.add(override)
    override.username = username or None
    override.anydesk = anydesk or None
    override.hostname = hostname
    override.ip = ip
    override.mac = mac
    db.session.commit()
    flash("Dados salvos para host {}".format(hostname), "success")
    return redirect(url_for("hosts.all_hosts"))
