from flask import Blueprint, render_template
from api.zabbix import get_hosts

hosts = Blueprint("hosts", __name__)

@hosts.route("/hosts")
def list_hosts():

    data = get_hosts()

    return render_template(
        "hosts.html",
        hosts=data
    )
