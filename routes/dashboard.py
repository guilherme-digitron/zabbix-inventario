from flask import Blueprint,render_template

from api.zabbix import get_hosts

dashboard=Blueprint("dashboard",__name__)

@dashboard.route("/")

def home():

    hosts=get_hosts()

    return render_template(
        "dashboard.html",
        hosts=hosts
    )
