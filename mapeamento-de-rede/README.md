Mapeamento de Rede — módulo leve integrado ao projeto

Instalação e execução:
1. Copie a pasta `mapeamento-de-rede` para a raiz do repositório.
2. Instale dependências Python (recomendo criar virtualenv):
   pip install -r mapeamento-de-rede/requirements.txt
3. Baixe o cytoscape.min.js (ou outra lib de grafos) e coloque em:
   mapeamento-de-rede/static/js/cytoscape.min.js
   (ex: https://unpkg.com/cytoscape/dist/cytoscape.min.js — preferencialmente faça o download e salve localmente)
4. Ajuste permissões/ACLs se necessário (ver instruções em Permissões.md abaixo).
5. Inicie sua aplicação Flask (seu app.py já existente deverá registrar o blueprint; ver patch).

Endpoints:
GET /rede -> UI
GET /api/rede/dispositivos
GET /api/rede/topologia
GET /api/rede/status
POST /api/rede/discover
GET /api/rede/device/<id>

Arquivo de DB:
mapeamento-de-rede/data/network.db

Permissões:
- nmap: algumas varreduras (-sV, -O) exigem privilégios; usamos varreduras leves (-sn e portas limitadas). Para permitir uso por usuário não-root:
  sudo setcap cap_net_raw,cap_net_admin+ep $(which nmap)
  (documentado abaixo — preferível revisar política de segurança)
