document.addEventListener('DOMContentLoaded', function() {
  const statusEl = document.getElementById('status');
  const btn = document.getElementById('btn-discover');

  function setStatus(s){ statusEl.textContent = s; }

  async function fetchTopo(){
    setStatus('Carregando topologia...');
    const r = await fetch('/api/rede/topologia');
    const topo = await r.json();
    setStatus('Mapeando grafos...');
    drawTopo(topo);
    setStatus('Pronto');
  }

  async function startDiscover(){
    setStatus('Iniciando descoberta...');
    await fetch('/api/rede/discover', {method: 'POST'});
    pollStatus();
  }

  btn.addEventListener('click', startDiscover);

  async function pollStatus(){
    setStatus('Mapeamento em andamento...');
    let s = await (await fetch('/api/rede/status')).json();
    const start = Date.now();
    function cont(){
      fetch('/api/rede/status').then(r=>r.json()).then(s=>{
        setStatus(`Descoberta: running=${s.running} devices=${s.devices} progress=${s.progress||0}%`);
        if(s.running) setTimeout(cont, 2000);
        else { fetchTopo(); }
      });
    }
    cont();
  }

  function drawTopo(topo){
    const elements = [];
    (topo.nodes||[]).forEach(n=>{
      elements.push({ data: { id: ''+n.id, label: n.hostname || n.ip }});
    });
    (topo.edges||[]).forEach(e=>{
      elements.push({ data: { id: 'e'+Math.random(), source: ''+e.source, target: ''+e.target, label: e.confidence }});
    });
    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: elements,
      style: [
        { selector: 'node', style: { 'label': 'data(label)', 'background-color': '#0074D9', 'color': '#fff', 'text-valign': 'center', 'text-outline-width': 2 }},
        { selector: 'edge', style: { 'width': 2, 'line-color': '#ccc', 'target-arrow-color': '#ccc', 'curve-style': 'bezier' }}
      ],
      layout: { name: 'cose' }
    });
    cy.on('tap', 'node', function(evt){
      const node = evt.target.data();
      fetch('/api/rede/dispositivos').then(r=>r.json()).then(list=>{
        const d = list.find(x=>x.ip===node.label || x.hostname===node.label);
        const panel = document.getElementById('details');
        if(d){
          panel.innerHTML = `<pre>${JSON.stringify(d, null, 2)}</pre>`;
        } else {
          panel.innerText = 'Detalhes não disponíveis';
        }
      });
    });
  }

  // inicial
  fetchTopo();
});
