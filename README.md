# Zabbix Inventário — trimmed to single dashboard

This repository was reduced to a minimal dashboard (the main and only screen).

To run locally:

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

The dashboard is available at http://localhost:5000/ and shows these columns only: hostname, IP, MAC address, modelo, OS.
