(()=>{const L=[['/forja','⚒','Forja'],['/transmutacao','🧪','Transmutação'],['/linhagens','🜂','Linhagens'],['/rituais-ancestrais','🔥','Rituais'],['/biblioteca-cartas','🃏','Biblioteca'],['/cartas-geradas','✦','Geradas'],['/atelie-arte','🎨','Ateliê'],['/tutorial','📖','Tutorial']];
const p=location.pathname.replace(/\/$/,'');const n=document.createElement('nav');n.className='sx-nav';n.setAttribute('aria-label','Sistemas do Coliseu');
n.innerHTML='<a class="sx-home" href="/">← Coliseu</a><div class="sx-tabs">'+L.map(([u,i,t])=>`<a href="${u}"${u===p?' class="on" aria-current="page"':''}><i>${i}</i>${t}</a>`).join('')+'</div>';
document.body.prepend(n);const a=n.querySelector('.on');if(a)a.scrollIntoView({inline:'center',block:'nearest'})})();
