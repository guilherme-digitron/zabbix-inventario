# Sistema de Descoberta, Inventário e Mapeamento de Rede TCP/IP

🌐 **Descoberta Automática de Rede com Visualização de Topologia**

Sistema completo, gratuito e open-source para descoberta automática/semi-automática de dispositivos em uma rede TCP/IP, com mapeamento visual de topologia e armazenamento de histórico.

## Características Principais

✅ **Descoberta de Dispositivos**
- Detecção de hosts ativos com Nmap, ARP e SNMP
- Identificação de IP, MAC address e hostname
- Identificação de fabricante pelo MAC (OUI)
- Detecção de portas abertas e serviços
- Tentativa de identificação do SO

✅ **Classificação de Dispositivos**
- Router/Gateway
- Switch gerenciável
- Access Point WiFi
- Servidor
- Desktop/Notebook
- Smartphone
- Impressora
- Dispositivos IoT
- Desconhecido

✅ **Mapeamento de Topologia**
- Detecção de conexões confirmadas (LLDP, CDP, SNMP, MAC table)
- Inferência de conexões por análise de dados
- Visualização interativa em SVG
- Diferenciação entre conexões confirmadas e inferidas
- Indicação de confiança de cada conexão

✅ **Histórico e Relatórios**
- Armazenamento de scans anteriores
- Histórico de alterações por dispositivo
- Detecção de dispositivos novos/removidos
- Detecção de mudanças de IP, MAC, hostname
- Timeline de eventos

✅ **Interface Web**
- Dashboard com resumo da rede
- Mapa visual interativo
- Lista de dispositivos filtrada
- Detalhes de cada dispositivo
- Histórico de scans
- Configurações do sistema

✅ **Agendamento**
- Scans automáticos em intervalo configurável
- Execução manual de scans
- Monitoramento do status de execução

## Requisitos

### Hardware
- Raspberry Pi 4 (recomendado) ou superior
- Mínimo 1GB RAM (2GB+ recomendado)
- Cartão microSD 8GB ou maior

### Sistema Operacional
- **Principal**: Raspberry Pi OS Lite (Debian)
- **Compatível**: Ubuntu 20.04+, Debian 11+
- **Experimental**: Windows 10+ (com Python 3.8+)

### Dependências
- Python 3.8+
- Nmap (recomendado)
- Flask (via pip)
- SQLite3 (incluído no Python)

## Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone https://github.com/seu-usuario/network-mapper.git
cd network-mapper
```

### 2. Instalação Automática (Debian/Ubuntu/Raspberry Pi)

```bash
sudo bash install.sh
```

Ou instalação manual:

```bash
# Atualizar sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar dependências
sudo apt-get install -y python3 python3-pip python3-venv nmap git curl

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências Python
pip install -r requirements.txt
```

### 3. Configuração Inicial

```bash
# Variáveis de ambiente (opcional)
export NETWORK_CIDR='192.168.1.0/24'    # Rede a escanear
export SCAN_INTERVAL='600'              # Intervalo em segundos (padrão: 10 min)
export NMAP_ENABLED='true'              # Habilitar Nmap
export ARP_ENABLED='true'               # Habilitar ARP
export LOG_LEVEL='INFO'                 # Nível de log
```

### 4. Iniciar a Aplicação

```bash
activate venv/bin/activate
python3 app.py
```

Acesse em:
```
http://IP_DO_RASPBERRY:5000/rede
```

## Uso

### Dashboard
Página principal com resumo da rede:
- Total de dispositivos
- Dispositivos online/offline
- Portas abertas
- Atividade recente

### Mapa de Topologia
Visualização interativa da rede:
- Clique em um dispositivo para ver detalhes
- Filtrar por tipo ou status
- Pesquisar dispositivo por IP ou hostname
- Linhas sólidas = conexões confirmadas
- Linhas tracejadas = conexões inferidas

### Dispositivos
Lista completa com informações:
- IP e Hostname
- Endereço MAC
- Tipo de dispositivo
- Status (online/offline)
- Portas abertas

### Histórico
Scans anteriores:
- Data/hora do scan
- Quantidade de dispositivos encontrados
- Status (completo/erro)
- Duração do scan

### Configurações
- CIDR da rede a scanear
- Intervalo de scans automáticos
- Habilitar/desabilitar scanners
- Habilitação do scheduler automático

## API REST

Todas as funcionalidades estão disponíveis via API REST em `/api/network`:

### Dispositivos
```bash
# Listar todos
GET /api/network/devices

# Obter um dispositivo
GET /api/network/devices/<ip>

# Filtrar por status
GET /api/network/devices/status/online
```

### Scans
```bash
# Iniciar scan manual
POST /api/network/scan
{
  "network_cidr": "192.168.1.0/24"
}

# Status do scan
GET /api/network/scan/status

# Listar scans anteriores
GET /api/network/scans?limit=10
```

### Topologia
```bash
# Obter topologia
GET /api/network/topology

# Status da rede
GET /api/network/network/status
```

### Configuração
```bash
# Obter config
GET /api/network/config

# Atualizar config
POST /api/network/config
{
  "network_cidr": "192.168.1.0/24",
  "scan_interval_seconds": 600,
  "scheduler_running": true
}
```

## Estrutura do Projeto

```
network-mapper/
├── app.py                          # Aplicação principal
├── requirements.txt                # Dependências Python
├── install.sh                      # Script de instalação
├── README.md                       # Este arquivo
│
├── network_discovery/              # Módulo principal
│   ├── __init__.py
│   ├── config.py                   # Configurações
│   ├── discovery_engine.py         # Motor de descoberta
│   ├── scheduler.py                # Agendador de scans
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # Modelos de dados
│   │   └── database.py             # Gerenciador do banco SQLite
│   │
│   ├── scanner/
│   │   ├── __init__.py
│   │   ├── base_scanner.py         # Classe base
│   │   ├── nmap_scanner.py         # Scanner Nmap
│   │   ├── arp_scanner.py          # Scanner ARP
│   │   └── snmp_scanner.py         # Scanner SNMP (em desenvolvimento)
│   │
│   ├── topology/
│   │   ├── __init__.py
│   │   ├── correlation.py          # Motor de correlação
│   │   ├── topology_engine.py      # Motor de topologia
│   │   └── graph_generator.py      # Gerador de gráficos SVG
│   │
│   └── api/
│       ├── __init__.py
│       ├── api.py                  # APIs REST
│       └── rede_blueprint.py       # Blueprint das páginas
│
├── templates/
│   ├── index.html                  # Página raiz
│   └── rede/
│       └── dashboard.html          # Dashboard principal
│
└── static/
    ├── css/
    │   ├── style.css               # Estilos globais
    │   └── dashboard.css           # Estilos do dashboard
    └── js/
        ├── api.js                  # Funções da API
        ├── dashboard.js            # Lógica do dashboard
        └── topology.js             # Visualização de topologia
```

## Configuração Avançada

### Nmap

```bash
# Instalar Nmap
sudo apt-get install nmap

# Dar permissões (se necessário)
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+ep /usr/bin/nmap
```

### SNMP

```bash
# Instalar ferramentas SNMP
sudo apt-get install snmp snmp-mibs-downloader

# Instalar biblioteca Python SNMP
pip install pysnmp
```

### Executar como Serviço Systemd

Criar arquivo `/etc/systemd/system/network-discovery.service`:

```ini
[Unit]
Description=Network Discovery and Topology Mapping
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/network-mapper
ExecStart=/home/pi/network-mapper/venv/bin/python3 /home/pi/network-mapper/app.py
Restart=on-failure
RestartSec=10
Environment="NETWORK_CIDR=192.168.1.0/24"
Environment="SCAN_INTERVAL=600"

[Install]
WantedBy=multi-user.target
```

Enabilitando:

```bash
sudo systemctl daemon-reload
sudo systemctl enable network-discovery
sudo systemctl start network-discovery
sudo systemctl status network-discovery
```

## Troubleshooting

### "Nmap não encontrado"
```bash
sudo apt-get install nmap
```

### "Permissão negada" ao executar Nmap
```bash
sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+ep /usr/bin/nmap
```

### Port 5000 já em uso
```bash
# Mudar porta em app.py ou usar:
PORT=8080 python3 app.py
```

### Banco de dados corrompido
```bash
rm network_discovery/data/network_discovery.db
python3 app.py  # Recriará o banco
```

### Verificar logs
```bash
tail -f network_discovery.log
```

## Desenvolvimento

### Ambiente de Desenvolvimento

```bash
pip install pytest pytest-cov flake8 black
```

### Executar Testes

```bash
pytest tests/
```

### Linting

```bash
flake8 network_discovery/
black network_discovery/
```

## Roadmap

- [ ] Interface de SNMP Query completa
- [ ] Detecção de LLDP/CDP
- [ ] Exportação de relatórios (PDF, CSV)
- [ ] Alertas e notificações
- [ ] Multi-usuário e autenticação
- [ ] Integração com Zabbix API
- [ ] Teste em mais plataformas
- [ ] Melhorias de UI/UX
- [ ] Caching de resultados
- [ ] Importação de subredes múltiplas

## Limitações

- Requer acesso à rede e permissões para ARP/SNMP
- Nmap requer privilégios elevados para algumas operações
- Topologia inferida pode não ser 100% precisa
- Não realiza exploração de vulnerabilidades (por design)
- Performance depende do tamanho da rede e recursos disponíveis

## Segurança

⚠️ **Importante**:
- Este sistema é para uso apenas em redes autorizadas
- Não realiza ataques, brute-force ou exploração de vulnerabilidades
- Credenciais SNMP devem ser mantidas seguras
- Use HTTPS em produção
- Restrinja o acesso à interface web com firewall ou autenticação

## Contribuindo

Contribuições são bem-vindas! Por favor:

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## Licença

Este projeto está sob licença MIT. Veja `LICENSE` para detalhes.

## Autores

- **Guilherme da Silva Cordeiro** - Desenvolvimento inicial
- Inspirado em ferramentas como Nmap, Netdot, Graphviz

## Contato

Para dúvidas, sugestões ou reportar bugs:
- Issues no GitHub
- Email: seu-email@exemplo.com

## Agradecimentos

- Comunidade do Nmap
- Comunidade Python
- Comunidade Raspberry Pi
- Todos os colaboradores

---

**Versão**: 1.0.0  
**Última atualização**: Setembro 2026  
**Status**: Ativo e em desenvolvimento
