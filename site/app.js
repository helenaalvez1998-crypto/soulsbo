const $ = (selector) => document.querySelector(selector);
const GWENT_ARENA_THEME_KEY = 'soulsbot.gwent.arena-theme';
function gwentEldenRingThemeEnabled() {
  try {
    return window.localStorage.getItem(GWENT_ARENA_THEME_KEY) === 'elden-ring';
  } catch (_) {
    return false;
  }
}
function applyGwentArenaTheme(enabled = gwentEldenRingThemeEnabled()) {
  const active = Boolean(enabled);
  document.body?.classList.toggle('gwent-theme-eldenring', active);
  document.documentElement?.classList.toggle('gwent-theme-eldenring', active);
  return active;
}
function updateGwentArenaThemeButton(button, enabled = gwentEldenRingThemeEnabled()) {
  if (!button) return;
  button.setAttribute('aria-pressed', String(Boolean(enabled)));
  button.textContent = enabled ? '✧ ELDEN RING · ATIVO' : '✧ TEMA ELDEN RING';
  button.classList.toggle('is-active', Boolean(enabled));
}
let collection = [];
let cardCatalog = [];
let currentUser = null;
const text = (value, fallback = '—') => value === null || value === undefined || value === '' ? fallback : String(value);
const number = (value) => new Intl.NumberFormat('pt-BR').format(Number(value || 0));
const isCardImageUrl = (value) => /\/api\/gwent\/(?:public-)?cards\/[^/]+\/image/.test(String(value || ''));
const imageUrl = (card) => {
  const cardId = card.card_id || String(card.id || '').split('::')[0];
  const raw = card.image_url || `/api/gwent/public-cards/${encodeURIComponent(cardId)}/image`;
  if (!isCardImageUrl(raw)) return raw;
  const url = new URL(raw, window.location.origin);
  // Compatibilidade com dados antigos: qualquer carta publicada usa rota pública.
  url.pathname = url.pathname.replace('/api/gwent/cards/', '/api/gwent/public-cards/');
  const rarity = card.raridade || card.rarity;
  const power = card.poder ?? card.power;
  if (rarity) url.searchParams.set('rarity', String(rarity));
  if (power !== null && power !== undefined && Number.isFinite(Number(power))) url.searchParams.set('power', String(Number(power)));
  // Grade/deck usam miniatura. O modal pede perfil HD independente.
  if (!url.searchParams.has('detail')) url.searchParams.set('thumb', '1');
  return `${url.pathname}${url.search}`;
};
const cardImageMarkup = (card, alt = '') =>
  `<img data-card-src="${escapeHTML(imageUrl(card))}" loading="lazy" decoding="async" alt="${escapeHTML(alt)}">`;
// V52 — linguagem visual semântica das cartas (ícones vetoriais locais, sem dependência externa).
const CARD_SIGILS = {
  'ordem áurea': '✦', 'véu carmesim': '血', 'lua negra': '☾', 'os esquecidos': '✝',
  'corpo a corpo': '⚔', 'longa distância': '➶', 'cerco': '⌖',
  'especial': '◇', 'relíquia': '♜', 'primordial': '✹'
};
const normalizeCardLabel = value => String(value || '').normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
const cardSigil = value => {
  const key = normalizeCardLabel(value);
  return CARD_SIGILS[key] || (key.includes('lua') ? '☾' : key.includes('sangue') ? '血'
    : key.includes('fogo') || key.includes('chama') ? '♨'
    : key.includes('gelo') || key.includes('geada') ? '❄'
    : key.includes('morte') || key.includes('exec') ? '†'
    : key.includes('invoc') || key.includes('espir') ? '♧'
    : key.includes('escud') || key.includes('protec') ? '⬡'
    : key.includes('venen') || key.includes('podrid') ? '☣'
    : key.includes('louc') || key.includes('frenes') ? '◉'
    : key.includes('cura') || key.includes('purif') ? '✧'
    : key.includes('Especial') ? '◇' : '✦');
};
const RARITY_POWER = {'Comum':0,'Rara':1,'Épica':2,'Lendária':3,'Mítica':4,'Primordial':5,'Singular':6};
const rarityPower = card => Number.isFinite(Number(card?.potencia_raridade)) ? Number(card.potencia_raridade) : (RARITY_POWER[card?.raridade] ?? 0);
const rarityPowerMarkup = card => `<span class=\"v54-rarity-power\" title=\"Potência da raridade: amplia habilidades; não é poder de ataque\"><i>✦</i> Potência ${rarityPower(card)}</span>`;
const cardInsigniaMarkup = card => {
  const category = card.categoria === 'Especial' ? 'Especial' : 'Unidade';
  const faction = card.faccao || 'Sem facção';
  const row = card.row_label || card.fileira || (category === 'Especial' ? 'Efeito' : 'Fileira não informada');
  const rarity = card.raridade || 'Comum';
  const ability = card.habilidade_nome || card.efeito_nome || card.habilidade || card.efeito || '';
  if (category === 'Especial') {
    const effect = card.habilidade_texto || card.texto_efeito || 'Efeito especial';
    return `<div class="v51-special-banner"><span><i>◇</i> CARTA ESPECIAL</span><span>${escapeHTML(rarity)}</span></div><div class="v54-card-rarity-line">${rarityPowerMarkup(card)}<small>Escala do efeito · não soma ao poder-base</small></div><div class="v51-card-bottomline v51-special-effect"><span title="${escapeHTML(effect)}"><i>${cardSigil(effect)}</i>${escapeHTML(effect)}</span></div>`;
  }
  return `<div class="v51-card-topline"><span class="v51-card-faction" title="${escapeHTML(faction)}"><i>${cardSigil(faction)}</i>${escapeHTML(faction)}</span><span class="v51-card-rarity">${escapeHTML(rarity)}</span></div><div class="v54-card-rarity-line">${rarityPowerMarkup(card)}<small>Escala do efeito · não soma ao poder-base</small></div><div class="v51-card-bottomline"><span title="${escapeHTML(row)}"><i>${cardSigil(row)}</i>${escapeHTML(row)}</span>${ability ? `<span class="v51-card-ability" title="${escapeHTML(ability)}"><i>${cardSigil(ability)}</i>${escapeHTML(ability)}</span>` : `<span class="v51-card-ability v51-no-ability"><i>—</i>Sem habilidade especial</span>`}</div>`;
};
const CARD_IMAGE_FALLBACK = `data:image/svg+xml,${encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 620"><rect width="420" height="620" rx="20" fill="#17131c"/><rect x="18" y="18" width="384" height="584" rx="16" fill="none" stroke="#9b805a" stroke-width="4"/><path d="M210 190l55 55-55 55-55-55z" fill="none" stroke="#9b805a" stroke-width="8"/><text x="210" y="390" fill="#d8c6a6" font-family="sans-serif" font-size="22" text-anchor="middle">ARTE INDISPONÍVEL</text><text x="210" y="425" fill="#978a9b" font-family="sans-serif" font-size="16" text-anchor="middle">Tente recarregar a página</text></svg>')}`;
const CARD_IMAGE_RETRY_DELAYS = [700, 1600];
const CARD_IMAGE_MAX_ACTIVE = 4;
const cardImageQueue = [];
let cardImageActive = 0;
function enqueueCardImage(image, source = image?.dataset.cardSrc) {
  if (!(image instanceof HTMLImageElement) || !source || image.dataset.cardImageFallback === 'true') return;
  if (image.dataset.cardImageQueued === 'true' || image.dataset.cardImageActive === 'true') return;
  image.dataset.cardPendingSrc = source;
  image.dataset.cardImageQueued = 'true';
  cardImageQueue.push(image);
  pumpCardImages();
}
function pumpCardImages() {
  while (cardImageActive < CARD_IMAGE_MAX_ACTIVE && cardImageQueue.length) {
    const image = cardImageQueue.shift();
    if (!(image instanceof HTMLImageElement) || !image.isConnected) continue;
    image.dataset.cardImageQueued = 'false';
    image.dataset.cardImageActive = 'true';
    cardImageActive += 1;
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      image.dataset.cardImageActive = 'false';
      cardImageActive = Math.max(0, cardImageActive - 1);
      pumpCardImages();
    };
    image.addEventListener('load', finish, {once:true});
    image.addEventListener('error', finish, {once:true});
    image.src = image.dataset.cardPendingSrc || image.dataset.cardSrc;
  }
}
let cardImageObserver = null;
if ('IntersectionObserver' in window) {
  cardImageObserver = new IntersectionObserver(entries => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      cardImageObserver.unobserve(entry.target);
      enqueueCardImage(entry.target);
    }
  }, {rootMargin:'360px 0px', threshold:0.01});
}
function observeCardImages(root) {
  if (!root) return;
  const images = [];
  if (root instanceof HTMLImageElement && root.hasAttribute('data-card-src')) images.push(root);
  if (root.querySelectorAll) images.push(...root.querySelectorAll('img[data-card-src]'));
  for (const image of images) {
    if (image.dataset.cardImageObserved === 'true') continue;
    image.dataset.cardImageObserved = 'true';
    if (cardImageObserver) cardImageObserver.observe(image);
    else enqueueCardImage(image);
  }
}
// Observa conteúdo dinâmico: a galeria só inicia as quatro imagens mais próximas da tela.
if (document.body && 'MutationObserver' in window) {
  const cardMutationObserver = new MutationObserver(records => {
    for (const record of records) for (const node of record.addedNodes) {
      if (node.nodeType === Node.ELEMENT_NODE) observeCardImages(node);
    }
  });
  cardMutationObserver.observe(document.body, {childList:true, subtree:true});
}
document.addEventListener('error', (event) => {
  const image = event.target;
  if (!(image instanceof HTMLImageElement) || !isCardImageUrl(image.src)) return;
  const attempts = Number(image.dataset.cardRetry || 0);
  if (attempts < CARD_IMAGE_RETRY_DELAYS.length) {
    image.dataset.cardRetry = String(attempts + 1);
    const original = image.dataset.cardOriginalSrc || image.dataset.cardSrc || image.src;
    image.dataset.cardOriginalSrc = original;
    window.setTimeout(() => {
      const retryUrl = new URL(original, window.location.origin);
      retryUrl.searchParams.set('_retry', String(attempts + 1));
      enqueueCardImage(image, `${retryUrl.pathname}${retryUrl.search}`);
    }, CARD_IMAGE_RETRY_DELAYS[attempts]);
    return;
  }
  image.dataset.cardImageFallback = 'true';
  image.src = CARD_IMAGE_FALLBACK;
  image.alt = 'Imagem da carta indisponível';
}, true);
function escapeHTML(value) { return String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function showNotice(message, kind = 'info') {
  const el = $('#notice'); if (el) { el.textContent = message; el.className = `notice ${kind}`; el.hidden = !message; }
  if (!message) return;
  let t = document.getElementById('toast');
  if (!t) { t = document.createElement('div'); t.id = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
  t.textContent = message; t.className = `toast ${kind} show`;
  clearTimeout(t._h); t._h = setTimeout(() => t.classList.remove('show'), 5000);
}
async function loadAccount() {
  try {
    const meResponse = await fetch('/api/me', {credentials:'same-origin', cache:'no-store'});
    if (!meResponse.ok) {
      currentUser = null;
      $('#profile-name').textContent = 'Visitante';
      $('#profile-status').textContent = 'Conecte sua conta Discord';
      $('#login-button').hidden = false; $('#logout-button').hidden = true;
      collection = [];
      cardCatalog = [];
      showNotice('Entre com sua conta Discord para acessar o Gwent.');
      return;
    }
    const me = await meResponse.json(); currentUser = me.user;
    $('#profile-name').textContent = $('#profile-name').dataset.n || 'Conta Discord';
    $('#profile-status').textContent = $('#profile-status').dataset.s || `ID ${text(currentUser?.id)}`;
    $('#login-button').hidden = true; $('#logout-button').hidden = false;
    const response = await fetch('/api/gwent/cards', {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha ao carregar cartas do Gwent.');
    collection = Array.isArray(data.cards) ? data.cards : [];
    cardCatalog = Array.isArray(data.catalog) ? data.catalog : [];
    $('#souls').textContent = number(data.summary?.souls);
    $('#fragments').textContent = number(data.summary?.fragments);
    $('#denarios').textContent = number(data.summary?.denarios);
    $('#gwent-xp').textContent = number(data.summary?.xp);
    showNotice(`Gwent sincronizado: ${collection.length} exemplares na coleção · ${cardCatalog.length} modelos no catálogo.`, 'success');
  } catch (error) { showNotice(error.message || 'Falha ao conectar ao servidor.', 'error'); }
}
$('#login-button').addEventListener('click', () => { const next = window.location.pathname + window.location.search; window.location.href = `/auth/discord/login?next=${encodeURIComponent(next)}`; });
$('#logout-button').addEventListener('click', async () => { await fetch('/auth/logout', {method:'POST', credentials:'same-origin'}); window.location.href = '/'; });

// --- Motor e interface do Gwent do Coliseu. ---
let gwentDeckIds = [];
let gwentSavedIds = [];
let gwentSavedFaction = 'Ordem Áurea';
let gwentSavedLeader = 'comandante_fornalha';
let gwentSavedRelic = '';
let gwentLeaderOptions = [];
let currentGwentMatch = null;
let currentGwentData = null;
let gwentMatchFinished = false;
let gwentPoll = null;
let gwentListPoll = null;
// Evita reconstruir a arena (e baixar novamente as imagens) quando o estado não mudou.
let gwentLastRenderSignature = '';
let gwentRefreshPromise = null;
let gwentRefreshEpoch = 0;
let gwentActionInFlight = false;
let gwentInitialSnapshotLoaded = false;
let gwentSeenRoundCount = 0;
let gwentPreviouslyFinished = false;
// null = automático. O padrão abre na preparação/vez do jogador e recolhe na vez adversária.
let gwentHandOpen = null;
let gwentHandLastPhase = null;
let gwentSelectedHandCard = '';
let gwentHandCardsById = new Map();
let gwentLastTurnAnnouncement = null;
let gwentLastViewportWidth = window.innerWidth;
let gwentHistoryPopoverCleanup = null;

const gwentRows = [
  ['melee', 'Corpo a corpo'], ['ranged', 'Longa distância'], ['siege', 'Cerco']
];

function updateGwentSelectedCardUI(cardId = gwentSelectedHandCard) {
  const arena = $('#gwent-arena');
  if (!arena) return;
  const id = String(cardId || '');
  const card = gwentHandCardsById.get(id) || null;
  gwentSelectedHandCard = card ? id : '';

  arena.querySelectorAll('[data-gwent-hand-card]').forEach(article => {
    const selected = article.dataset.gwentHandCard === gwentSelectedHandCard;
    article.classList.toggle('is-selected', selected);
    article.setAttribute('aria-pressed', String(selected));
  });

  const name = arena.querySelector('#gwent-selected-name');
  const effect = arena.querySelector('#gwent-selected-effect');
  const detail = arena.querySelector('[data-gwent-selected-details]');
  const row = arena.querySelector('#gwent-selected-row');
  const play = arena.querySelector('[data-gwent-play-selected]');
  const preview = arena.querySelector('#gwent-selected-card-image');

  if (name) name.textContent = card ? (card.nome || 'Carta selecionada') : 'Selecione uma carta';
  if (effect) effect.textContent = card
    ? `${card.habilidade_nome || 'Habilidade'} · ${card.habilidade_texto || 'Sem efeito adicional'}${card.especial ? ' · Carta especial' : ` · ${number(card.poder)} poder`}`
    : 'Clique em uma carta para configurar a jogada.';
  if (detail) detail.hidden = !card;
  if (preview) {
    const handImage = card
      ? arena.querySelector(`[data-gwent-hand-card="${CSS.escape(id)}"] img[data-card-src]`)
      : null;
    preview.replaceChildren(handImage ? handImage.cloneNode(true) : document.createTextNode(''));
    preview.hidden = !card;
  }
  if (row) {
    row.disabled = !card || row.dataset.turnAllowed !== 'true';
    if (card && card.row && [...row.options].some(option => option.value === card.row)) row.value = card.row;
  }
  if (play) play.disabled = !card || play.dataset.turnAllowed !== 'true';
}

const gwentFactionInfo = {
  'Ordem Áurea': { description: 'Luz, lei e fé: defesa, juramentos, proteção e purificação.', leaders: [
    ['comandante_fornalha', 'Godfrey', 'Fortalece +2 todas as unidades aliadas de Corpo a Corpo.'],
    ['bastiao_ancestral', 'Morgott', 'Concede Escudo e +1 a até 2 aliados da fileira escolhida.'],
    ['juiz_cerco', 'Radagon', 'Purifica estados negativos; cada aliado purificado recebe +1.']
  ]},
  'Lua Negra': { description: 'Magia, cosmos e segredos: feitiçaria, gravidade e domínio astral.', leaders: [
    ['arquimaga_eclipse', 'Rennala', 'Remove Geada e Podridão dos aliados; aliados purificados em Cerco recebem +1.'],
    ['mestre_eclipse', 'Astel', 'Aplica Geada aos 3 inimigos mais fortes da fileira escolhida.'],
    ['oraculo_tempestade', 'Loretta', 'Concede +2 às 2 unidades aliadas mais fortes de Longa Distância.']
  ]},
  'Véu Carmesim': { description: 'Sangue, sacrifício e heresia: hemorragia, devoção e corrupção.', leaders: [
    ['mestre_veu', 'Mohg', 'Aplica marcas de Sangramento aos 2 inimigos mais fortes da fileira.'],
    ['sombra_caminhante', 'Rykard', 'Sacrifica o aliado mais fraco e fortalece os demais da fileira.'],
    ['voz_caidos', 'Esgar', 'Ressuscita uma unidade de poder-base até 5 do descarte.']
  ]},
  'Os Esquecidos': { description: 'Fé, devoção e glória: evangelho, irmandade e fortalecimento das unidades esquecidas.', leaders: [
    ['lider_papa_esquecido', 'Papa Esquecido', 'Concede +1 de bônus às unidades dos Esquecidos na fileira escolhida.']
  ]}
};
// Os líderes vêm do servidor (fonte única); a lista fixa acima serve só de reserva se a API não enviar.
function applyGwentLeaders(byFaction) {
  if (!byFaction) return;
  Object.entries(byFaction).forEach(([faction, list]) => {
    if (!Array.isArray(list) || !list.length || !gwentFactionInfo[faction]) return;
    gwentFactionInfo[faction].leaders = list.map(l => [l.id, l.name, l.description, l.art_url || '', l.default_art_url || '']);
  });
}
function renderGwentLeaderOptions(selected = '') {
  const faction = $('#gwent-faction')?.value || 'Ordem Áurea';
  const info = gwentFactionInfo[faction] || gwentFactionInfo['Ordem Áurea'];
  const select = $('#gwent-leader');
  if (!select) return;
  select.innerHTML = info.leaders.map(([id, name]) => `<option value="${id}">${escapeHTML(name)}</option>`).join('');
  select.value = info.leaders.some(([id]) => id === selected) ? selected : info.leaders[0][0];
  $('#gwent-faction-description').textContent = info.description;
  const leader = info.leaders.find(([id]) => id === select.value) || info.leaders[0];
  const leaderHelp = $('#gwent-leader-description');
  if (leaderHelp) leaderHelp.textContent = `${leader[1]}: ${leader[2]}`;
  const preview = $('#gwent-leader-card');
  if (preview) {
    const sigils = {'Ordem Áurea':'✧','Véu Carmesim':'♜','Lua Negra':'☾','Os Esquecidos':'✝'};
    const factionClass = {'Ordem Áurea':'gold','Véu Carmesim':'blood','Lua Negra':'moon','Os Esquecidos':'faith'}[faction] || 'gold';
    const hasCustomArt = !!leader[3];
    const artUrl = leader[3] || leader[4] || '';
    const artValue = artUrl ? `url('${escapeHTML(artUrl)}')` : 'none';
    preview.innerHTML = `<div class="gwent-leader-relic v52-leader-card faction-${factionClass} ${hasCustomArt ? 'has-custom-leader-art' : ''}" style="--leader-art:${artValue}"><div class="leader-art-backdrop" aria-hidden="true"></div><div class="leader-relic-sigil">${sigils[faction] || '✦'}</div><small>${escapeHTML(faction)}</small><strong>${escapeHTML(leader[1])}</strong><p>${escapeHTML(leader[2])}</p><em>LÍDER · CARTA DE COMANDO</em></div>`;
  }
}
function renderGwentBuilder() {
  const selected = gwentDeckIds.map(id => collection.find(c => c.id === id)).filter(Boolean);
  const evolutionCost = {Comum:20, Rara:40, 'Épica':80, 'Lendária':160};
  const upgradeCost = {Comum:10, Rara:20, 'Épica':40, 'Lendária':80, 'Mítica':150, 'Primordial':250};
  const specialCount = selected.filter(card => card.categoria === 'Especial').length;
  const unitCount = selected.length - specialCount;
  $('#gwent-deck-count').textContent = `${selected.length}/12 cartas · ${unitCount} unidades · ${specialCount} especiais`;
  const cardTile = (card, inDeck = false) => inDeck
    ? `<button type="button" class="gwent-card-tile gwent-deck-mini is-selected" data-gwent-inspect="${escapeHTML(card.id)}" aria-label="Inspecionar ${escapeHTML(card.nome)}" title="Clique para ver detalhes"><span class="gwent-card-tile-art">${cardImageMarkup(card, card.nome || 'Carta')}</span><span class="gwent-deck-mini-name">${escapeHTML(card.nome || 'Carta')}</span></button>`
    : `<button type="button" class="gwent-card-tile" data-gwent-inspect="${escapeHTML(card.id)}" aria-label="Inspecionar ${escapeHTML(card.nome)}" title="Clique para ver detalhes"><span class="gwent-card-tile-art">${cardImageMarkup(card, card.nome || 'Carta')}</span><span class="gwent-card-tile-hint">VER CARTA</span></button>`;
  $('#gwent-deck-selected').innerHTML = selected.map(card => cardTile(card, true)).join('') || '<div class="empty-state">Selecione 12 cartas da coleção.</div>';
  const q = ($('#gwent-card-search').value || '').trim().toLocaleLowerCase('pt-BR');
  const selectedSet = new Set(selected.map(card => card.card_id || card.id));
  const factionFilter = $('#gwent-filter-faction')?.value || '';
  const rarityFilter = $('#gwent-filter-rarity')?.value || '';
  const pool = collection.filter(c => !selectedSet.has(c.card_id || c.id)
    && (!factionFilter || c.faccao === factionFilter)
    && (!rarityFilter || c.raridade === rarityFilter)
    && (`${c.nome} ${c.faccao} ${c.row_label || c.fileira} ${c.papel_gwent} ${c.categoria} ${c.habilidade} ${c.habilidade_texto} ${c.descricao}`.toLocaleLowerCase('pt-BR').includes(q)));
  $('#gwent-card-pool').innerHTML = pool.map(card => cardTile(card)).join('') || '<div class="empty-state">Nenhuma carta disponível na sua coleção com esses filtros.</div>';
  renderGwentCatalog();
  const selectedFaction = $('#gwent-faction')?.value || 'Ordem Áurea';
  const factionAliases = {'Lua Sombria':'Lua Negra','Casa Cariana':'Lua Negra','Dinastia Mohgwyn':'Véu Carmesim','Fé':'Os Esquecidos'};
  const factionCounts = {'Ordem Áurea':0,'Véu Carmesim':0,'Lua Negra':0,'Os Esquecidos':0};
  selected.filter(card => card.categoria !== 'Especial').forEach(card => {
    const rawFaction = card.faccao || '';
    const faction = factionAliases[rawFaction] || (Object.prototype.hasOwnProperty.call(factionCounts, rawFaction) ? rawFaction : '');
    if (Object.prototype.hasOwnProperty.call(factionCounts, faction)) factionCounts[faction] += 1;
  });
  const maxFactionCount = Math.max(...Object.values(factionCounts));
  const factionMatches = maxFactionCount > 0 && factionCounts[selectedFaction] === maxFactionCount;
  const configChanged = selectedFaction !== gwentSavedFaction
    || ($('#gwent-leader')?.value || 'comandante_fornalha') !== gwentSavedLeader
    || ($('#gwent-relic-select')?.value || '') !== gwentSavedRelic;
  $('#gwent-save-deck').disabled = selected.length !== 12 || unitCount < 8 || specialCount > 4 || !factionMatches
    || (JSON.stringify(gwentDeckIds) === JSON.stringify(gwentSavedIds) && !configChanged);
  const resetButton = $('#gwent-reset-deck');
  if (resetButton) resetButton.disabled = selected.length === 0 && gwentSavedIds.length === 0;
  $('#gwent-deck-status').textContent = selected.length === 12 && unitCount < 8
    ? 'Inclua pelo menos 8 unidades no deck.'
    : specialCount > 4 ? 'O limite é de 4 cartas especiais por deck.'
    : selected.length === 12 && !factionMatches
      ? `A facção escolhida precisa ser predominante: Ordem Áurea ${factionCounts['Ordem Áurea']} · Véu Carmesim ${factionCounts['Véu Carmesim']} · Lua Negra ${factionCounts['Lua Negra']} · Os Esquecidos ${factionCounts['Os Esquecidos']}.`
      : `${unitCount}/12 unidades e ${specialCount}/4 especiais. Facção predominante: ${selectedFaction}.`;
}


function renderGwentCatalog() {
  const target = $('#gwent-catalog-pool');
  if (!target) return;
  const q = ($('#gwent-card-search')?.value || '').trim().toLocaleLowerCase('pt-BR');
  const factionFilter = $('#gwent-filter-faction')?.value || '';
  const rarityFilter = $('#gwent-filter-rarity')?.value || '';
  const ownedIds = new Set(collection.map(card => String(card.card_id || card.id || '').split('::')[0]));
  const pool = cardCatalog.filter(card =>
    (!factionFilter || card.faccao === factionFilter)
    && (!rarityFilter || card.raridade === rarityFilter)
    && (`${card.nome} ${card.faccao} ${card.row_label || card.fileira} ${card.papel_gwent} ${card.categoria} ${card.habilidade_nome} ${card.habilidade_texto}`.toLocaleLowerCase('pt-BR').includes(q))
  );
  const ownedCount = pool.filter(card => ownedIds.has(String(card.card_id || card.id))).length;
  const count = $('#gwent-catalog-count');
  if (count) count.textContent = `${pool.length} modelos · ${ownedCount} na coleção · ${pool.length - ownedCount} não obtidos`;
  target.innerHTML = pool.map(card => {
    const cardId = String(card.card_id || card.id || '');
    const owned = ownedIds.has(cardId);
    return `<article class="gwent-catalog-card ${owned ? 'is-owned' : 'is-locked'}" tabindex="0" role="button" data-gwent-inspect="${escapeHTML(cardId)}" aria-label="Ver detalhes de ${escapeHTML(card.nome || 'Carta')}"><div class="gwent-catalog-art">${cardImageMarkup(card, card.nome || 'Carta')}</div><div class="gwent-catalog-meta"><b>${escapeHTML(card.nome || 'Carta')}</b><small>${escapeHTML(card.raridade || 'Comum')} · ${escapeHTML(card.faccao || 'Sem facção')}</small><span class="gwent-catalog-state">${owned ? '✓ Na sua coleção' : 'Ainda não obtida'}</span><span class="gwent-catalog-open">Ver detalhes</span></div></article>`;
  }).join('') || '<p class="muted">Nenhuma carta corresponde aos filtros.</p>';
  observeCardImages(target);
}
function closeGwentCollectionCardModal() {
  document.getElementById('gwent-collection-card-modal')?.remove();
}
function openGwentCollectionCardModal(cardId) {
  const ownedCard = collection.find(item => String(item.id) === String(cardId))
    || collection.find(item => String(item.card_id || '') === String(cardId));
  const catalogCard = cardCatalog.find(item => String(item.card_id || item.id || '') === String(cardId));
  const card = ownedCard || catalogCard;
  if (!card) return;
  closeGwentCollectionCardModal();
  const isOwned = !!ownedCard;
  const deckCardId = ownedCard ? String(ownedCard.id) : '';
  const inDeck = !!deckCardId && gwentDeckIds.includes(deckCardId);
  const special = card.categoria === 'Especial';
  const abilityName = card.habilidade_nome || card.efeito_nome || (special ? 'Efeito especial' : 'Sem habilidade especial');
  const abilityText = card.habilidade_texto || card.texto_efeito || (special ? 'Efeito não informado.' : 'Esta unidade não possui habilidade especial.');
  const rarityBudget = rarityPower(card);
  const src = imageUrl(card);
  const modalCard = {...card};
  if (isCardImageUrl(src)) {
    const hi = new URL(src, window.location.origin);
    hi.searchParams.delete('thumb');
    hi.searchParams.set('detail', '1');
    modalCard.image_url = `${hi.pathname}${hi.search}`;
  }
  const modal = document.createElement('div');
  modal.id = 'gwent-collection-card-modal';
  modal.className = 'gwent-collection-card-modal';
  modal.setAttribute('role','dialog');
  modal.setAttribute('aria-modal','true');
  modal.setAttribute('aria-label',`Detalhes da carta ${card.nome || ''}`);
  const tags = [
    card.raridade || 'Comum',
    card.faccao || 'Sem facção',
    special ? 'Especial' : (card.row_label || card.fileira || 'Unidade')
  ];
  const combos = Array.isArray(card.combos_compativeis) ? card.combos_compativeis : [];
  const synergies = Array.isArray(card.sinergias) ? card.sinergias : [];
  modal.innerHTML = `
    <section class="gwent-collection-card-dialog">
      <button type="button" class="gwent-collection-close" data-gwent-collection-close aria-label="Fechar">×</button>
      <div class="gwent-collection-art-column">
        <div class="gwent-collection-art">${cardImageMarkup(modalCard, card.nome || 'Carta')}</div>
        <strong class="gwent-collection-card-name">${escapeHTML(card.nome || 'Carta')}</strong>
        <small>${isOwned ? `EXEMPLAR #${number(card.exemplar_id || 0)}` : 'MODELO GLOBAL · AINDA NÃO OBTIDA'}</small>
      </div>
      <div class="gwent-collection-info">
        <header>
          <small class="eyebrow">ARQUIVO DO COLISEU · FICHA DA CARTA</small>
          <h2>${escapeHTML(card.nome || 'Carta')}</h2>
          <div class="gwent-collection-tags">${tags.map(tag=>`<span>${escapeHTML(tag)}</span>`).join('')}</div>
        </header>
        <section class="gwent-collection-power">
          <div><small>PODER-BASE</small><strong>${special ? '—' : number(card.poder)}</strong></div>
          <div><small>PODER MÁXIMO</small><strong>${special ? '—' : number(card.max_power || card.poder)}</strong></div>
          <div><small>POTÊNCIA DA RARIDADE</small><strong>${number(rarityBudget)} / 6</strong></div>
        </section>
        <section class="gwent-collection-section gwent-collection-effect">
          <small>EFEITO DE COMBATE</small>
          <h3>${escapeHTML(abilityName)}</h3>
          <p>${escapeHTML(abilityText)}</p>
        </section>
        ${card.descricao ? `<section class="gwent-collection-section"><small>LORE</small><p class="gwent-collection-lore">${escapeHTML(card.descricao)}</p></section>` : ''}
        ${(synergies.length || combos.length) ? `<section class="gwent-collection-section"><small>SINERGIAS</small>${synergies.length ? `<div class="gwent-collection-chips">${synergies.map(x=>`<span>${escapeHTML(x)}</span>`).join('')}</div>` : ''}${combos.map(x=>`<article class="gwent-collection-combo"><b>${escapeHTML(x.nome || 'Combo')}</b><p>${escapeHTML(x.descricao || '')}</p></article>`).join('')}</section>` : ''}
        <footer class="gwent-collection-actions">
          ${!isOwned
            ? `<p class="muted">Obtenha um exemplar em pacotes ou recompensas para adicioná-lo ao seu deck.</p>`
            : inDeck
              ? `<button type="button" class="secondary" data-gwent-collection-remove="${escapeHTML(deckCardId)}">REMOVER DO DECK</button>`
              : `<button type="button" class="primary" data-gwent-collection-add="${escapeHTML(deckCardId)}" ${gwentDeckIds.length >= 12 ? 'disabled' : ''}>ADICIONAR AO DECK</button>`}
        </footer>
      </div>
    </section>`;
  document.body.appendChild(modal);
  observeCardImages(modal);
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('[data-gwent-collection-close]')) closeGwentCollectionCardModal();
  });
  modal.querySelector('[data-gwent-collection-close]')?.focus();
}
document.addEventListener('click', event => {
  const inspect = event.target.closest('[data-gwent-inspect]');
  if (inspect) { openGwentCollectionCardModal(inspect.dataset.gwentInspect); return; }
  const add = event.target.closest('[data-gwent-collection-add]');
  if (add) {
    const cardId = add.dataset.gwentCollectionAdd;
    const card = collection.find(item => String(item.id) === String(cardId));
    const selected = gwentDeckIds.map(id => collection.find(item => item.id === id)).filter(Boolean);
    if (gwentDeckIds.length >= 12) return showNotice('O deck já possui 12 cartas.', 'error');
    if (selected.some(item => (item.card_id || item.id) === (card?.card_id || card?.id))) return showNotice('O deck não pode repetir o mesmo modelo.', 'error');
    if (card?.categoria === 'Especial' && selected.filter(item => item.categoria === 'Especial').length >= 4) return showNotice('O deck aceita no máximo quatro cartas especiais.', 'error');
    gwentDeckIds.push(cardId);
    closeGwentCollectionCardModal();
    renderGwentBuilder();
    return;
  }
  const remove = event.target.closest('[data-gwent-collection-remove]');
  if (remove) {
    gwentDeckIds = gwentDeckIds.filter(id => id !== remove.dataset.gwentCollectionRemove);
    closeGwentCollectionCardModal();
    renderGwentBuilder();
  }
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closeGwentCollectionCardModal();
  const catalogCard = event.target.closest('.gwent-catalog-card[data-gwent-inspect]');
  if (catalogCard && (event.key === 'Enter' || event.key === ' ')) {
    event.preventDefault();
    openGwentCollectionCardModal(catalogCard.dataset.gwentInspect);
  }
});
let atelierPromptText = '';
let atelierNegativeText = '';
let atelierAnalysisText = '';
let atelierReferenceUrl = '';
let atelierPreviewUrl = '';


function atelierReferenceForFaction(faction) {
  const value = String(faction || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  if (value.includes('ordem aurea')) return '/assets/atelier-referencias/ordem-aurea.png';
  if (value.includes('lua negra')) return '/assets/atelier-referencias/lua-negra.png';
  if (value.includes('veu carmesim')) return '/assets/atelier-referencias/veu-carmesim.png';
  if (value.includes('esquecidos')) return '/assets/atelier-referencias/os-esquecidos.png';
  return '';
}

function atelierEscapeHtml(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'
  }[ch]));
}

function atelierBlobAsDataUrl(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ''));
    reader.onerror = () => reject(new Error('Não foi possível preparar a imagem da referência.'));
    reader.readAsDataURL(blob);
  });
}

async function atelierEnsurePng(blob) {
  if (blob.type === 'image/png') return blob;
  const bitmap = await createImageBitmap(blob);
  try {
    const canvas = document.createElement('canvas');
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Não foi possível preparar a imagem da referência.');
    context.drawImage(bitmap, 0, 0);
    return await new Promise((resolve, reject) => {
      canvas.toBlob(result => result
        ? resolve(result)
        : reject(new Error('Não foi possível converter a referência para PNG.')), 'image/png');
    });
  } finally {
    bitmap.close?.();
  }
}


function atelierDownloadBlob(blob, filename) {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  link.style.display = 'none';
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
}

function atelierCopyPlainText(text) {
  if (navigator.clipboard?.writeText) {
    return navigator.clipboard.writeText(text);
  }
  const field = document.createElement('textarea');
  field.value = text;
  field.setAttribute('readonly', '');
  field.style.cssText = 'position:fixed;left:-10000px;top:0;opacity:0;';
  document.body.appendChild(field);
  field.select();
  let ok = false;
  try { ok = document.execCommand('copy'); } catch { ok = false; }
  field.remove();
  return ok ? Promise.resolve() : Promise.reject(new Error('O navegador bloqueou a cópia dos prompts.'));
}

function atelierLegacyRichCopy(html) {
  const container = document.createElement('div');
  container.contentEditable = 'true';
  container.setAttribute('aria-hidden', 'true');
  container.style.cssText = 'position:fixed;left:-10000px;top:0;width:800px;background:#fff;color:#000;';
  container.innerHTML = html;
  document.body.appendChild(container);
  const selection = window.getSelection();
  const range = document.createRange();
  range.selectNodeContents(container);
  selection.removeAllRanges();
  selection.addRange(range);
  let copied = false;
  try { copied = document.execCommand('copy'); } catch { copied = false; }
  selection.removeAllRanges();
  container.remove();
  return copied;
}

function selectedAtelierTarget() {
  const raw = String($('#atelier-card')?.value || '');
  const splitAt = raw.lastIndexOf('|');
  if (splitAt <= 0) return null;
  const cardId = raw.slice(0, splitAt);
  const exemplarId = Number(raw.slice(splitAt + 1));
  return cardId && Number.isInteger(exemplarId) && exemplarId > 0 ? {cardId, exemplarId} : null;
}

function renderAtelierCardOptions() {
  const select = $('#atelier-card');
  if (!select) return;
  const exemplars = collection.filter(card => Number.isInteger(Number(card.exemplar_id)) && Number(card.exemplar_id) > 0);
  select.innerHTML = '<option value="">Selecione um exemplar</option>' + exemplars.map(card => {
    const cardId = String(card.card_id || card.id || '');
    const exemplarId = Number(card.exemplar_id);
    const maxPower = Number(card.max_power ?? card.maxPower ?? card.poder_maximo ?? card.poder ?? 0);
    const power = Number(card.poder ?? card.power ?? 0);
    return `<option value="${escapeHTML(`${cardId}|${exemplarId}`)}">${escapeHTML(card.nome || cardId)} · Exemplar #${exemplarId} · ${escapeHTML(card.raridade || card.rarity || 'Comum')} · Poder ${power}/${maxPower}</option>`;
  }).join('');
}

async function loadAtelierHistory() {
  const target = $('#atelier-history');
  if (!target || !currentUser) return;
  try {
    const response = await fetch('/api/gwent/atelier/history', {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível carregar o histórico do Ateliê.');
    target.innerHTML = (data.history || []).map(item => {
      const labels = {pending:'Em análise', approved:'Aprovada · arte oficial', rejected:'Rejeitada', archived:'Arquivada · não está mais aplicada à carta'};
      return `<article class="atelier-history-item"><b>${escapeHTML(item.card_id)}${item.exemplar_id ? ` · Exemplar #${Number(item.exemplar_id)}` : ' · arte legada por modelo'}</b><span>${escapeHTML(labels[item.status] || item.status)}</span><small>${escapeHTML(item.created_at || '')}</small>${item.rejection_reason ? `<p>${escapeHTML(item.rejection_reason)}</p>` : ''}</article>`;
    }).join('') || '<p class="muted">Você ainda não enviou ilustrações.</p>';
  } catch (error) { target.innerHTML = `<p class="muted">${escapeHTML(error.message)}</p>`; }
}

async function loadAtelierReviewQueue() {
  const panel = $('#atelier-review-panel');
  if (!panel || !currentUser) return;
  try {
    const response = await fetch('/api/gwent/atelier/review', {credentials:'same-origin', cache:'no-store'});
    if (response.status === 403) { panel.hidden = true; return; }
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha ao consultar a fila.');
    panel.hidden = false;
    await loadAtelierLeaderArtAdmin();
    $('#atelier-review-queue').innerHTML = (data.pending || []).map(item =>
      `<article class="atelier-review-item"><img src="/api/gwent/atelier/submission/${Number(item.id)}/image" loading="lazy" decoding="async" alt="Carta completa submetida"><div><b>${escapeHTML(item.card_id)} · ${item.exemplar_id ? `Exemplar #${Number(item.exemplar_id)}` : 'Arte por modelo (legada)'}</b><small>Artista: ${escapeHTML(item.artist_name || `Discord ${item.user_id}`)}</small><small>${escapeHTML(item.created_at || '')}</small><div class="atelier-review-actions"><button class="primary" type="button" data-atelier-approve="${Number(item.id)}">Aprovar</button><button class="secondary" type="button" data-atelier-reject="${Number(item.id)}">Rejeitar</button></div></div></article>`
    ).join('') || '<p class="muted">Nenhuma arte aguardando aprovação.</p>';
  } catch (error) { panel.hidden = true; showNotice(error.message, 'error'); }
}

let atelierAdminLeaderArts = [];

function selectedAdminLeaderArt() {
  const id = $('#atelier-leader-art-select')?.value || '';
  return atelierAdminLeaderArts.find(item => item.id === id) || null;
}

function updateAtelierLeaderArtPreview() {
  const leader = selectedAdminLeaderArt();
  const preview = $('#atelier-leader-art-preview');
  const empty = $('#atelier-leader-art-empty');
  const remove = $('#atelier-leader-art-remove');
  const upload = $('#atelier-leader-art-upload');
  if (!leader) {
    if (preview) preview.hidden = true;
    if (empty) { empty.hidden = false; empty.textContent = 'Selecione um líder.'; }
    if (remove) remove.hidden = true;
    if (upload) upload.disabled = true;
    return;
  }
  const source = leader.art_url || leader.default_art_url || '';
  if (source && preview) {
    preview.src = source;
    preview.hidden = false;
  } else if (preview) preview.hidden = true;
  if (empty) empty.hidden = !!source;
  if (remove) remove.hidden = !leader.has_art;
  if (upload) upload.disabled = false;
  const status = $('#atelier-leader-art-status');
  if (status) status.textContent = leader.has_art
    ? `Arte personalizada ativa${leader.artist_name ? ` · crédito: ${leader.artist_name}` : ''}. Uma nova imagem substituirá a atual.`
    : 'Retrato padrão em uso. Envie uma imagem para aplicar uma arte personalizada.';
}

async function loadAtelierLeaderArtAdmin() {
  const select = $('#atelier-leader-art-select');
  if (!select) return;
  const response = await fetch('/api/gwent/atelier/leaders', {credentials:'same-origin', cache:'no-store'});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Não foi possível carregar as cartas de líder.');
  atelierAdminLeaderArts = data.leaders || [];
  const previous = select.value;
  select.innerHTML = atelierAdminLeaderArts.map(leader =>
    `<option value="${escapeHTML(leader.id)}">${escapeHTML(leader.name)} · ${escapeHTML(leader.faction)}${leader.has_art ? ' · arte personalizada' : ''}</option>`
  ).join('');
  if (atelierAdminLeaderArts.some(leader => leader.id === previous)) select.value = previous;
  else if (atelierAdminLeaderArts.length) select.value = atelierAdminLeaderArts[0].id;

  const byFaction = {};
  atelierAdminLeaderArts.forEach(leader => {
    if (!byFaction[leader.faction]) byFaction[leader.faction] = [];
    byFaction[leader.faction].push({id:leader.id,name:leader.name,description:leader.description,art_url:leader.art_url,default_art_url:leader.default_art_url});
  });
  applyGwentLeaders(byFaction);
  if ($('#gwent-leader')) renderGwentLeaderOptions($('#gwent-leader').value);
  updateAtelierLeaderArtPreview();
}

async function uploadAtelierLeaderArt() {
  const leader = selectedAdminLeaderArt();
  const file = $('#atelier-leader-art-file')?.files?.[0];
  const status = $('#atelier-leader-art-status');
  const button = $('#atelier-leader-art-upload');
  if (!leader) return;
  if (!file) { if (status) status.textContent = 'Selecione uma imagem antes de aplicar.'; return; }
  const form = new FormData();
  form.append('image', file);
  form.append('artist_name', $('#atelier-leader-art-credit')?.value || '');
  if (button) { button.disabled = true; button.textContent = 'Aplicando arte…'; }
  try {
    const response = await fetch(`/api/gwent/atelier/leaders/${encodeURIComponent(leader.id)}/art`, {
      method:'POST', credentials:'same-origin', body:form
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível aplicar a arte ao líder.');
    if (status) status.textContent = `${data.message} ${data.width} × ${data.height}px.`;
    $('#atelier-leader-art-file').value = '';
    await loadAtelierLeaderArtAdmin();
    showNotice(`Arte de ${leader.name} atualizada para todos os jogadores.`, 'success');
  } catch (error) {
    if (status) status.textContent = error.message;
    showNotice(error.message, 'error');
  } finally {
    if (button) { button.disabled = false; button.textContent = 'Aplicar arte ao líder'; }
    updateAtelierLeaderArtPreview();
  }
}

async function removeAtelierLeaderArt() {
  const leader = selectedAdminLeaderArt();
  if (!leader || !leader.has_art) return;
  if (!window.confirm(`Restaurar a arte padrão de ${leader.name}? A imagem personalizada deixará de aparecer na carta de líder.`)) return;
  const button = $('#atelier-leader-art-remove');
  if (button) { button.disabled = true; button.textContent = 'Restaurando…'; }
  try {
    const response = await fetch(`/api/gwent/atelier/leaders/${encodeURIComponent(leader.id)}/art`, {
      method:'DELETE', credentials:'same-origin', headers:{'Content-Type':'application/json'}
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível restaurar a arte padrão.');
    await loadAtelierLeaderArtAdmin();
    showNotice(`Retrato padrão de ${leader.name} restaurado.`, 'success');
  } catch (error) {
    const status = $('#atelier-leader-art-status');
    if (status) status.textContent = error.message;
    showNotice(error.message, 'error');
  } finally {
    if (button) { button.disabled = false; button.textContent = 'Restaurar arte padrão'; }
  }
}

async function removeAllAtelierArts() {
  const confirmed = window.confirm(
    'Remover todas as artes oficiais atualmente aplicadas às cartas?\n\n' +
    'As cartas voltarão à arte-base. O histórico, os créditos dos artistas e os arquivos enviados serão preservados. Esta ação não pode ser desfeita pelo site.'
  );
  if (!confirmed) return;
  const button = $('#atelier-remove-all-art');
  if (button) { button.disabled = true; button.textContent = 'Removendo artes...'; }
  try {
    const response = await fetch('/api/gwent/atelier/remove-all-art', {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'}, body: '{}'
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível remover as artes oficiais.');
    await Promise.all([loadAtelierHistory(), loadAtelierOfficialArt()]);
    const cards = Number(data.cartas_limpas || 0);
    const arts = Number(data.artes_removidas || 0);
    showNotice(`${arts} arte(s) retirada(s) de ${cards} carta(s). Histórico e arquivos preservados.`, 'success');
  } catch (error) {
    showNotice(error.message, 'error');
  } finally {
    if (button) { button.disabled = false; button.textContent = 'Remover todas as artes aplicadas'; }
  }
}

async function loadAtelier() {
  if (!currentUser) return;
  renderAtelierCardOptions();
  await Promise.all([loadAtelierHistory(), loadAtelierReviewQueue(), loadAtelierOfficialArt()]);
}

async function loadAtelierOfficialArt() {
  const selected = selectedAtelierTarget();
  const target = $('#atelier-official-art');
  if (!target) return;
  if (!selected) { target.innerHTML = '<p class="muted">Selecione um exemplar para verificar sua carta completa.</p>'; return; }
  try {
    const response = await fetch(`/api/gwent/atelier/official/${encodeURIComponent(selected.cardId)}?exemplar_id=${selected.exemplarId}`, {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Falha ao consultar arte oficial.');
    target.innerHTML = data.official
      ? `<img class="atelier-official-preview" loading="lazy" decoding="async" src="${escapeHTML(data.image_url)}" alt="Carta completa oficial"><small>Carta completa do exemplar #${selected.exemplarId} · artista <b>${escapeHTML(data.artist_name)}</b> · ${escapeHTML(data.created_at)}</small>`
      : `<p class="muted">O exemplar #${selected.exemplarId} ainda utiliza a arte-base. Envie uma carta completa para este exemplar.</p>`;
  } catch (error) { target.innerHTML = `<p class="muted">${escapeHTML(error.message)}</p>`; }
}

async function generateAtelierPrompt() {
  const selected = selectedAtelierTarget();
  if (!selected) return showNotice('Selecione um exemplar específico da sua coleção.', 'error');
  const {cardId, exemplarId} = selected;
  const button = $('#atelier-generate-prompt');
  button.disabled = true;
  try {
    const response = await fetch(`/api/gwent/atelier/prompt?card_id=${encodeURIComponent(cardId)}&exemplar_id=${exemplarId}`, {
      credentials: 'same-origin',
      cache: 'no-store'
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível gerar o prompt.');

    const selectedCard = collection.find(card => String(card.card_id || card.id) === String(cardId) && Number(card.exemplar_id) === exemplarId);
    const faction = data.faction || data.facção || selectedCard?.faccao || selectedCard?.faction || '';
    atelierPromptText = String(data.prompt || '').trim();
    atelierAnalysisText = String(data.analysis || '').trim();
    atelierNegativeText = '';
    atelierReferenceUrl = String(data.reference_url || '').trim() || atelierReferenceForFaction(faction);

    $('#atelier-analysis').value = atelierAnalysisText;
    $('#atelier-prompt').value = atelierPromptText;
    $('#atelier-negative').value = atelierReferenceUrl;

    const refPreview = $('#atelier-reference-preview');
    if (refPreview) {
      refPreview.onerror = () => {
        refPreview.hidden = true;
        showNotice('Não foi possível carregar a imagem de referência desta facção.', 'error');
      };
      refPreview.src = atelierReferenceUrl;
      refPreview.hidden = !atelierReferenceUrl;
    }

    $('#atelier-copy-prompt').disabled = !(atelierAnalysisText && atelierPromptText && atelierReferenceUrl);
    const promptsReady = Boolean(atelierAnalysisText && atelierPromptText);
    const referenceReady = Boolean(atelierReferenceUrl);
    $('#atelier-copy-prompts').disabled = !promptsReady;
    $('#atelier-copy-reference').disabled = !referenceReady;
    const copyReady = promptsReady && referenceReady;
    showNotice(
      copyReady
        ? `Prompts da carta completa do exemplar #${exemplarId} e referência de ${faction || 'facção'} carregados.`
        : 'Confira se a análise, o prompt fixo e a referência foram carregados.',
      copyReady ? 'success' : 'warning'
    );
  } catch (error) {
    atelierPromptText = '';
    atelierAnalysisText = '';
    atelierReferenceUrl = '';
    $('#atelier-copy-prompts').disabled = true; $('#atelier-copy-reference').disabled = true;
    showNotice(error.message, 'error');
  } finally {
    button.disabled = false;
  }
}

async function submitAtelierArt() {
  const selected = selectedAtelierTarget();
  const file = $('#atelier-image').files?.[0];
  if (!selected || !file) return showNotice('Selecione o exemplar e a imagem da carta completa.', 'error');
  const {cardId, exemplarId} = selected;
  if (!atelierPromptText) return showNotice('Gere o prompt individual da carta antes de enviar.', 'error');
  if (file.size > 8 * 1024 * 1024) return showNotice('A imagem ultrapassa o limite de 8 MB.', 'error');
  const form = new FormData(); form.append('card_id', cardId); form.append('exemplar_id', String(exemplarId)); form.append('prompt_text', `ANÁLISE ARTÍSTICA (PT)\n${atelierAnalysisText}\n\nPROMPT FIXO\n${atelierPromptText}\n\nREFERÊNCIA VISUAL\n${$('#atelier-negative').value}`); form.append('artist_name', ($('#atelier-artist-name').value || '').trim()); form.append('image', file);
  const button = $('#atelier-submit'); button.disabled = true;
  try {
    const response = await fetch('/api/gwent/atelier/submit', {method:'POST', credentials:'same-origin', body:form});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível enviar a carta completa.');
    showNotice(`Carta completa do exemplar #${exemplarId} enviada para aprovação · submissão #${data.submission_id}.`, 'success');
    $('#atelier-image').value = ''; $('#atelier-preview').hidden = true;
    await loadAtelierHistory(); await loadAtelierReviewQueue();
  } catch (error) { showNotice(error.message, 'error'); }
  finally { button.disabled = false; }
}

async function decideAtelierSubmission(id, approve) {
  document.querySelectorAll('[data-atelier-approve],[data-atelier-reject]').forEach(b => b.disabled = true);
  let reason = '';
  if (!approve) { reason = window.prompt('Informe o motivo da rejeição (opcional):', '') ?? null; if (reason === null) { await loadAtelierReviewQueue(); return; } }
  try {
    const response = await fetch(`/api/gwent/atelier/review/${id}`, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:JSON.stringify({approve, reason})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível registrar a decisão.');
    showNotice(approve ? 'Carta completa aprovada e publicada para o exemplar selecionado.' : 'Carta completa rejeitada; o motivo foi registrado.', 'success');
    await loadAtelierReviewQueue();
    await loadAtelierOfficialArt();
  } catch (error) { showNotice(error.message, 'error'); await loadAtelierReviewQueue(); }
}

async function loadGwentStore() {
  if (!currentUser) return;
  const status = $('#gwent-store-status');
  const packContainer = $('#gwent-pack-options');
  try {
    const response = await fetch('/api/gwent/store', {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível carregar o mercado.');
    const balance = Number(data.summary?.denarios || 0);
    $('#gwent-store-wallet').textContent = `${number(balance)} Denários disponíveis`;
    const packs = Array.isArray(data.packs) ? data.packs : [];
    if (packContainer) {
      const icons = {'Ordem Áurea':'☀','Véu Carmesim':'🩸','Lua Negra':'☾','Os Esquecidos':'✝'};
      packContainer.innerHTML = packs.map(pack => {
        const faction = pack.faction || '';
        const price = Number(pack.price || 120);
        const canBuy = balance >= price;
        const label = canBuy ? `Comprar · ${number(price)} Denários` : 'Denários insuficientes';
        return `<article class="gwent-store-card gwent-pack-option ${faction ? 'faction-pack' : ''}">
          <div class="pack-crest">${faction ? (icons[faction] || '✦') : '✦'}</div>
          <span class="pack-tag">${faction ? 'PACOTE DE FACÇÃO' : 'PACOTE GERAL'}</span>
          <h4>${escapeHTML(pack.name || 'Pacote do Coliseu')}</h4>
          <p>${escapeHTML(pack.description || 'Três cartas para sua coleção.')}</p>
          <small class="pack-pool">${number(pack.card_pool || 0)} modelos elegíveis · ${number(pack.cards || 3)} cartas por pacote</small>
          <button class="primary" type="button" data-buy-pack data-pack-faction="${escapeHTML(faction)}" ${canBuy ? '' : 'disabled'}>${label}</button>
        </article>`;
      }).join('');
    }
    if (status) status.textContent = 'Compre quantos pacotes quiser. Não existe limite diário; cada pacote custa 120 Denários e entrega 3 cartas. A proteção de raridade continua compartilhada entre os pacotes.';
  } catch (error) { if (status) status.textContent = error.message; }
}

async function buyGwentPack(faction = null, triggerButton = null) {
  const button = triggerButton || $('#gwent-open-pack');
  if (!button || button.disabled || !currentUser) return;
  const packageName = faction ? `Pacote ${faction}` : 'Pacote do Coliseu';
  if (!window.confirm(`Comprar ${packageName} com 3 cartas por 120 Denários?`)) return;
  button.disabled = true;
  const status = $('#gwent-store-status');
  try {
    const response = await fetch('/api/gwent/store/pack', {
      method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({faction})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível comprar o pacote.');
    const cards = Array.isArray(data.cards) ? data.cards : [];
    const factionLine = data.faccao ? `<p class="muted">${escapeHTML(data.faccao)}</p>` : '';
    $('#gwent-pack-results').innerHTML = `<div class="gwent-pack-opened"><h4>${escapeHTML(packageName)} aberto</h4>${factionLine}<div class="gwent-pack-opened-cards">${cards.map(card => `<article class="pk" data-r="${escapeHTML(String(card.rarity||'comum').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g,''))}"><b>${escapeHTML(card.card_name || card.card_id)}</b><span>${escapeHTML(card.rarity)} · ${number(card.power)} poder</span><small>${card.outcome === 'carta' ? 'Novo exemplar' : card.outcome === 'almas' ? `Duplicata · +${number(card.almas)} Almas` : `Duplicata · +${number(card.fragmentos)} fragmentos`}</small></article>`).join('')}</div></div>`;
    revealPack();
    showNotice('Pacote comprado e aberto. As cartas já estão na sua coleção.', 'success');
    await loadAccount(); await loadGwentStore(); await loadDropHistory();
  } catch (error) {
    showNotice(error.message, 'error');
    if (status) status.textContent = error.message;
    await loadGwentStore();
  }
}

async function loadDropHistory() {
  const target = $('#gwent-drop-history');
  if (!target || !currentUser) return;
  try {
    const response = await fetch('/api/gwent/drops/history', {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível carregar o histórico.');
    const history = Array.isArray(data.history) ? data.history : [];
    const movements = Array.isArray(data.movements) ? data.movements : [];
    const entries = [
      ...history.map(item => ({...item, entry_type:'drop'})),
      ...movements.map(item => ({...item, entry_type:'movement'})),
    ].sort((a,b) => String(b.created_at || '').localeCompare(String(a.created_at || '')));
    target.innerHTML = entries.map(item => {
      if (item.entry_type === 'movement') {
        const evolved = item.action === 'evolucao';
        const title = evolved ? 'Carta evoluída' : 'Carta lapidada';
        const detail = evolved
          ? `${item.rarity_before} → ${item.rarity_after} · -${number(item.amount)} fragmentos`
          : `${item.rarity_after} · ${number(item.power_before)} → ${number(item.power_after)} poder · -${number(item.amount)} Almas`;
        return `<article class="gwent-drop-history-item"><div><b>${escapeHTML(title)}</b><small>${escapeHTML(item.card_name || item.card_id || 'Carta')} · ${escapeHTML(detail)}</small></div><strong>#${number(item.exemplar_id)}</strong></article>`;
      }
      const outcome = item.outcome === 'revertido' ? 'Recompensa revertida'
        : item.outcome === 'almas' ? `Duplicata · +${number(item.almas_delta)} Almas`
        : item.outcome === 'fragmentos' ? `Duplicata · +${number(item.fragmentos_delta)} fragmentos`
        : item.outcome === 'singular' ? 'Feito especial · Singular conquistada'
        : item.outcome === 'singular_ja_possui' ? 'Feito especial · Singular já conquistada'
        : 'Carta adicionada à coleção';
      const sourceNames = {zerado:'Jogo zerado', platina:'Platina', run:'Run Soulslike', comunidade:'Comunidade', port:'Port enviado', mod:'Mod enviado', boas_vindas:'Boas-vindas', patente:'Patente', feito_singular:'Feito especial'};
      const source = sourceNames[item.origin] || (item.origin ? item.origin.replaceAll('_', ' ') : 'Atividade');
      return `<article class="gwent-drop-history-item"><div><b>${escapeHTML(item.card_name || 'Carta')}</b><small>${escapeHTML(item.rarity || 'Comum')} · ${escapeHTML(outcome)} · ${escapeHTML(source)}</small></div><strong>${item.power ? `${number(item.power)} poder` : ''}</strong></article>`;
    }).join('') || '<p class="muted">Ainda não há movimentações registradas.</p>';
  } catch (error) { target.innerHTML = `<p class="muted">${escapeHTML(error.message)}</p>`; }
}

async function loadGwentDeck() {
  if (!currentUser) return;
  try {
    const r = await fetch('/api/gwent/deck', {credentials:'same-origin', cache:'no-store'});
    const data = await parseGwentApiResponse(r);
    if (!r.ok) throw new Error(data.error || 'Não foi possível carregar o deck Gwent.');
    gwentSavedIds = (data.deck || []).map(c => c.id);
    gwentDeckIds = [...gwentSavedIds];
    gwentSavedFaction = data.faction || 'Ordem Áurea';
    gwentSavedLeader = data.leader_id || 'comandante_fornalha';
    gwentSavedRelic = data.relic_id || '';
    const relicSelect = $('#gwent-relic-select');
    if (relicSelect) {
      const ownedRelics = Array.isArray(data.relics) ? data.relics : [];
      const options = ['<option value="">Sem Relíquia</option>'];
      for (const relic of ownedRelics) {
        const label = relic.owned
          ? `${relic.name} · ${relic.rarity} · Possuída (${number(relic.owned_count)})`
          : `${relic.name} · ${relic.rarity} · Não obtida`;
        options.push(`<option value="${escapeHTML(relic.id)}" ${relic.owned ? '' : 'disabled'}>${escapeHTML(label)}</option>`);
      }
      relicSelect.innerHTML = options.join('');
      const savedIsOwned = ownedRelics.some(relic => relic.id === gwentSavedRelic && relic.owned);
      relicSelect.value = savedIsOwned ? gwentSavedRelic : '';
      relicSelect.dispatchEvent(new Event('change', {bubbles:true}));
      const relicStatus = $('#gwent-relic-status');
      if (relicStatus && !ownedRelics.some(relic => relic.owned)) {
        relicStatus.textContent = 'Você ainda não possui Relíquias. Elas têm 0,50% de chance em cada drop de carta.';
      }
    }
    applyGwentLeaders(data.leaders_by_faction);
    $('#gwent-faction').value = gwentSavedFaction;
    renderGwentLeaderOptions(gwentSavedLeader);
    $('#gwent-deck-status').textContent = gwentSavedIds.length === 12 ? 'Deck carregado.' : 'Monte seu deck Gwent com 12 cartas únicas para liberar a arena.';
    renderGwentBuilder();
  } catch (e) { $('#gwent-deck-status').textContent = e.message; }
}

async function saveGwentDeck() {
  const button = $('#gwent-save-deck'); button.disabled = true; button.textContent = 'Salvando...';
  try {
    const r = await fetch('/api/gwent/deck', {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:JSON.stringify({cards:gwentDeckIds.map(key => { const card = collection.find(c => c.id === key); return {card_id:card?.card_id || card?.id, exemplar_id:Number(card?.exemplar_id || 0)}; }), faction:$('#gwent-faction').value, leader_id:$('#gwent-leader').value, relic_id:$('#gwent-relic-select')?.value || ''})});
    const data = await parseGwentApiResponse(r); if (!r.ok) throw new Error(data.error || 'Falha ao salvar deck.');
    gwentSavedIds = [...gwentDeckIds]; gwentSavedFaction = $('#gwent-faction').value; gwentSavedLeader = $('#gwent-leader').value; gwentSavedRelic = $('#gwent-relic-select')?.value || '';
    $('#gwent-deck-status').textContent = 'Deck, facção e líder salvos. Seu exército está pronto para a arena.';
    showNotice('Deck Gwent atualizado.', 'success');
  } catch(e) { $('#gwent-deck-status').textContent = e.message; }
  finally { button.textContent = 'Salvar deck Gwent'; renderGwentBuilder(); }
}

async function resetGwentDeck() {
  if (!window.confirm('Redefinir seu deck Gwent? Todas as 12 posições e a configuração de facção, líder e relíquia serão zeradas. Suas cartas continuarão na coleção.')) return;
  const button = $('#gwent-reset-deck');
  if (button) { button.disabled = true; button.textContent = 'Zerando...'; }
  try {
    const response = await fetch('/api/gwent/deck/reset', {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'}, body: '{}'
    });
    const data = await parseGwentApiResponse(response);
    if (!response.ok) throw new Error(data.error || 'Não foi possível redefinir o deck.');
    try { localStorage.removeItem('narabot_gwent_relic_loadout_v20'); } catch (_) {}
    const relic = $('#gwent-relic-select');
    if (relic) {
      relic.value = '';
      relic.dispatchEvent(new Event('change', {bubbles: true}));
    }
    await loadGwentDeck();
    showNotice('Deck zerado. Suas cartas continuam disponíveis na coleção.', 'success');
  } catch (error) {
    $('#gwent-deck-status').textContent = error.message;
    showNotice(error.message, 'error');
  } finally {
    if (button) button.textContent = 'Redefinir deck';
    renderGwentBuilder();
  }
}

async function loadGwentMatches() {
  if (!currentUser) return;
  try {
    const r = await fetch('/api/gwent/matches', {credentials:'same-origin', cache:'no-store'}); const data = await r.json();
    if (!r.ok) throw new Error(data.error || 'Falha ao carregar partidas.');
    const rank = data.ranking || {mmr:1000,wins:0,losses:0,draws:0,tier:'Bronze'};
    const leaderboard = `<article class="duel-item gwent-leaderboard"><div><small class="eyebrow">TOP 10 DO SERVIDOR</small><h3>Classificação</h3><p>${(data.leaderboard || []).map((p,i) => `${i+1}. ${escapeHTML(p.name)} — ${number(p.mmr)} MMR`).join('<br>') || 'Ainda sem partidas ranqueadas.'}</p></div></article>`;
    const matchCards = (data.matches || []).map(m => {
      const isCreator = m.creator_id === String(currentUser.id);
      const isAI = Boolean(m.is_ai_match) || String(m.opponent_id) === '-1';
      const role = isAI ? 'Modo solo · Adversária: NARA IA' : (isCreator ? 'Você enviou o convite' : 'Você recebeu o convite');
      if (m.status === 'pending') {
        const controls = isCreator
          ? '<span class="muted">Aguardando resposta</span><button class="secondary" data-gwent-respond="cancel" data-match-id="' + m.id + '">Cancelar convite</button>'
          : '<button class="primary" data-gwent-respond="accept" data-match-id="' + m.id + '">Aceitar</button><button class="secondary" data-gwent-respond="decline" data-match-id="' + m.id + '">Recusar</button>';
        return `<article class="duel-item"><div><small class="eyebrow">CONVITE #${number(m.id)}</small><h3>Desafio aguardando resposta</h3><p>${role} · ${escapeHTML(m.created_at || '')}</p></div><div class="duel-controls">${controls}</div></article>`;
      }
      if (m.status === 'active') return `<article class="duel-item ${isAI ? 'gwent-ai-match' : ''}"><div><small class="eyebrow">GWENT #${number(m.id)}${isAI ? ' · TREINO' : ''}</small><h3>${isAI ? 'Treino contra NARA' : 'Partida em andamento'}</h3><p>${role} · ${escapeHTML(m.created_at || '')}</p></div><button class="primary" data-gwent-open="${m.id}">${isAI ? 'Continuar treino' : 'Abrir arena'}</button></article>`;
      const statusLabel = isAI ? 'Treino contra NARA · Finalizado' : (m.status === 'finished' ? 'Finalizada' : m.status === 'declined' ? 'Convite recusado' : m.status === 'cancelled' ? 'Convite cancelado' : 'Partida encerrada');
      return `<article class="duel-item ${isAI ? 'gwent-ai-match' : ''}"><div><small class="eyebrow">GWENT #${number(m.id)}${isAI ? ' · TREINO' : ''}</small><h3>${statusLabel}</h3><p>${role} · ${escapeHTML(m.created_at || '')}</p></div>${m.status === 'finished' ? `<button class="secondary" data-gwent-open="${m.id}">Ver resultado</button>` : ''}</article>`;
    }).join('');
    $('#gwent-match-list').innerHTML = `<article class="duel-item gwent-rank"><div><small class="eyebrow">SEU RANKING</small><h3>${escapeHTML(rank.tier)} · ${number(rank.mmr)} MMR</h3><p>${number(rank.wins)} vitórias · ${number(rank.losses)} derrotas · ${number(rank.draws)} empates</p></div><span>MMR Elo variável por resultado</span></article>` + leaderboard + (matchCards || '<div class="empty-state">Nenhuma partida Gwent registrada.</div>');
  } catch(e) { $('#gwent-match-list').innerHTML = `<div class="empty-state">${escapeHTML(e.message)}</div>`; }
}

async function createGwentMatch() {
  const opponent_id = $('#gwent-opponent').value;
  if (!opponent_id) return showNotice('Selecione um adversário.', 'error');
  if (gwentSavedIds.length !== 12) return showNotice('Salve primeiro um deck Gwent com 12 cartas.', 'error');
  const button = $('#gwent-create-match'); button.disabled = true;
  try {
    const r = await fetch('/api/gwent/matches', {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:JSON.stringify({opponent_id})});
    const data = await r.json(); if (!r.ok) throw new Error(data.error || 'Não foi possível iniciar partida.');
    showNotice('Convite enviado. A partida só começa quando o adversário aceitar.', 'success');
    await loadGwentMatches();
  } catch(e) { showNotice(e.message, 'error'); }
  finally { button.disabled = false; }
}


async function createGwentSoloMatch() {
  if (gwentSavedIds.length !== 12) return showNotice('Salve primeiro um deck Gwent com 12 cartas.', 'error');
  const button = $('#gwent-solo-match');
  if (!button) return;
  button.disabled = true;
  const originalText = button.textContent;
  button.textContent = 'Preparando adversária…';
  try {
    const response = await fetch('/api/gwent/matches/solo', {
      method: 'POST', credentials: 'same-origin',
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify({difficulty: 'normal'})
    });
    const data = await parseGwentApiResponse(response);
    if (!response.ok) throw new Error(data.error || 'Não foi possível iniciar o treino contra a NARA.');
    showNotice('A NARA está pronta. Boa partida.', 'success');
    await loadGwentMatches();
    await openGwentMatch(data.match_id);
  } catch (error) {
    showNotice(error.message || 'Falha ao iniciar partida solo.', 'error');
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

function gwentEffectivePower(card, weatherValue = 0) {
  const weatherPenalty = Math.max(0, Number(weatherValue || 0) - Number(card.weather_resist || 0));
  const statusPenalty = Math.min(3,
    Number(card.geada || 0) + Number(card.podrida || 0) + Number(card.loucura || 0)
  );
  return Math.max(1, Number(card.poder || 0) + Number(card.bonus || 0) - weatherPenalty - statusPenalty);
}
function gwentCardView(card, isEntering = false, weatherValue = 0, previousPower = null) {
  const power = gwentEffectivePower(card, weatherValue);
  const hasPowerDelta = previousPower !== null && previousPower !== undefined && Number.isFinite(Number(previousPower));
  const powerDelta = hasPowerDelta ? power - Number(previousPower) : 0;
  const powerDeltaClass = powerDelta > 0 ? 'has-power-up' : powerDelta < 0 ? 'has-power-down' : '';
  const powerDeltaMarkup = powerDelta ? `<span class="gwent-power-delta ${powerDelta > 0 ? 'is-up' : 'is-down'}">${powerDelta > 0 ? '+' : ''}${number(powerDelta)}</span>` : '';
  const statuses = [
    ['sangramento', '🩸', 'Sangramento'],
    ['geada', '❄️', 'Geada'],
    ['podrida', '🌺', 'Podridão Escarlate'],
    ['loucura', '🔥', 'Loucura']
  ].filter(([key]) => Number(card[key] || 0) > 0)
    .map(([key, glyph, label]) => `<i class="gwent-status" title="${label} ×${number(card[key])}">${glyph}</i>`).join('');
  // Cada camada visual nasce do estado real serializado da unidade. Não depende
  // de textos do histórico nem da identificação indireta da carta que aplicou o efeito.
  const statusVfx = [
    ['sangramento', 'bleeding'],
    ['geada', 'frost'],
    ['podrida', 'rot'],
    ['loucura', 'madness'],
    ['escudo', 'shield']
  ].map(([key, effect]) => {
    const level = Math.max(0, Math.min(2, Number(card[key] || 0)));
    return level > 0
      ? `<span class="gwent-unit-vfx gwent-unit-vfx--${effect}" data-level="${level}" aria-hidden="true"></span>`
      : '';
  }).join('');
  const title = `${card.nome || 'Carta'} · ${power} poder efetivo · ${card.row_label || ''}${Number(card.escudo || 0) > 0 ? ' · Escudo' : ''}`;
  return `<article class="gwent-board-card ${isEntering ? 'is-entering' : ''} ${powerDeltaClass}" data-card-id="${escapeHTML(card.id)}" data-row="${escapeHTML(card.row || '')}" role="button" tabindex="0" aria-label="Inspecionar ${escapeHTML(card.nome || 'carta')}, ${power} de poder efetivo" title="${escapeHTML(title)}">${cardImageMarkup(card, card.nome || 'Carta')}${statusVfx}<span class="gwent-board-power">${power}</span>${powerDeltaMarkup}<span class="gwent-statuses">${statuses}</span>${Number(card.escudo || 0) > 0 ? '<i class="gwent-shield" title="Escudo">◆</i>' : ''}</article>`;
}

let gwentAlvos = {};
let gwentBoardCardsById = new Map();
let gwentPreviousPowerSnapshot = new Map();
let gwentLastRenderedMatch = null;
let gwentLastRenderedRound = null;
const gwentRowLabel = (key) => (gwentRows.find(([k]) => k === key) || [key, key])[1];
function gwentOpcoesDoAlvo(cardId, row) {
  const info = gwentAlvos[cardId];
  if (!info) return null;
  const opcoes = (info.opcoes || []).filter(o => info.filtro_fileira === 'mesma' ? o.row === row
    : info.filtro_fileira === 'diferente' ? o.row !== row : true);
  return {...info, opcoes};
}
function closeGwentTargetPicker() { document.getElementById('gwent-target-modal')?.remove(); }
function openGwentTargetPicker(cardId, row, info) {
  closeGwentTargetPicker();
  const modal = document.createElement('div');
  modal.id = 'gwent-target-modal'; modal.className = 'gwent-target-modal';
  modal.setAttribute('role', 'dialog'); modal.setAttribute('aria-modal', 'true');
  modal.innerHTML = `<div class="gwent-target-box"><h3>${escapeHTML(info.rotulo || 'Escolha o alvo')}</h3><div class="gwent-target-list">${
    info.opcoes.map(o => `<button type="button" class="gwent-target-option" data-gwent-target="${escapeHTML(o.id)}"><b>${escapeHTML(o.nome)}</b><small>${number(o.poder + o.bonus)} poder · ${escapeHTML(gwentRowLabel(o.row))}${o.escudo > 0 ? ' · Escudo' : ''}</small></button>`).join('')
  }</div><div class="gwent-target-actions"><button type="button" class="secondary" data-gwent-target="">Automático</button><button type="button" class="secondary" data-gwent-target-cancel>Cancelar</button></div></div>`;
  modal.addEventListener('click', ev => {
    if (ev.target === modal || ev.target.closest('[data-gwent-target-cancel]')) return closeGwentTargetPicker();
    const choice = ev.target.closest('[data-gwent-target]');
    if (!choice) return;
    closeGwentTargetPicker();
    sendGwentAction('play', cardId, row, [], choice.dataset.gwentTarget || '');
  });
  document.addEventListener('keydown', function onEsc(ev) {
    if (ev.key === 'Escape') { closeGwentTargetPicker(); document.removeEventListener('keydown', onEsc); }
  });
  document.body.appendChild(modal);
  modal.querySelector('button')?.focus();
}


const GWENT_LEADER_DEFAULT_ARTS = {
  comandante_fornalha: 'godfrey', bastiao_ancestral: 'morgott', juiz_cerco: 'radagon',
  mestre_veu: 'mohg', sombra_caminhante: 'rykard', voz_caidos: 'esgar',
  lider_papa_esquecido: 'esgar', arquimaga_eclipse: 'rennala',
  mestre_eclipse: 'astel', oraculo_tempestade: 'loretta'
};
function gwentLeaderArtMarkup(leaderId, extraClass = '') {
  const id = String(leaderId || '');
  const fallback = GWENT_LEADER_DEFAULT_ARTS[id] || 'godfrey';
  const custom = `/api/gwent/leaders/${encodeURIComponent(id)}/art`;
  const defaultArt = `/assets/leaders/${fallback}.webp`;
  return `<img class="${escapeHTML(extraClass)}" src="${custom}" data-default-art="${defaultArt}" alt="Retrato do líder" loading="lazy" onerror="if(this.dataset.defaultTried!=='1'){this.dataset.defaultTried='1';this.src=this.dataset.defaultArt;}else{this.hidden=true;this.nextElementSibling.hidden=false;}">`;
}

const GWENT_LEADER_ICONS = {
  comandante_fornalha: '⚔', bastiao_ancestral: '🛡', juiz_cerco: '☀',
  mestre_veu: '🩸', sombra_caminhante: '🔥', voz_caidos: '†',
  lider_papa_esquecido: '✝', arquimaga_eclipse: '☾', mestre_eclipse: '✦',
  oraculo_tempestade: '➶'
};
const GWENT_LEADER_ROW_CHOICES = new Set([
  'bastiao_ancestral','mestre_veu','sombra_caminhante','voz_caidos',
  'lider_papa_esquecido','mestre_eclipse'
]);
const GWENT_LEADER_SIMPLE = {
  comandante_fornalha: 'Todas as suas unidades que estão em Corpo a Corpo ficam 2 pontos mais fortes.',
  bastiao_ancestral: 'Na fileira escolhida, até duas unidades suas mais fortes que ainda não têm Escudo recebem proteção e +1 de força.',
  juiz_cerco: 'Remove Sangramento, Geada, Podridão e Loucura de suas unidades. Cada unidade que for limpa ganha +1 de força.',
  mestre_veu: 'Na fileira escolhida, marca até duas unidades inimigas mais fortes com Sangramento. Uma segunda marca causa Hemorragia e tira 2 de bônus.',
  sombra_caminhante: 'Na fileira escolhida, sacrifica sua unidade mais fraca. Depois, suas outras unidades dessa fileira ganham +2 de bônus.',
  voz_caidos: 'Pega do seu descarte a unidade mais forte com poder-base 5 ou menos e coloca na fileira escolhida com +1 de bônus.',
  lider_papa_esquecido: 'Todas as suas unidades dos Esquecidos na fileira escolhida ganham +1 de bônus.',
  arquimaga_eclipse: 'Remove Geada e Podridão das suas unidades. As que forem limpas em Cerco ganham +1 de bônus.',
  mestre_eclipse: 'Na fileira escolhida, até três unidades inimigas mais fortes recebem uma marca de Geada.',
  oraculo_tempestade: 'As duas unidades suas mais fortes de Longa Distância ganham +2 de bônus.'
};
function gwentLeaderIcon(leaderId) { return GWENT_LEADER_ICONS[String(leaderId || '')] || '♜'; }
function gwentLeaderSimpleExplanation(leaderId, fallback = '') {
  return GWENT_LEADER_SIMPLE[String(leaderId || '')] || fallback || 'Ativa a habilidade especial do líder. Consulte a descrição para ver os alvos e as condições.';
}
function closeGwentLeaderModal() { document.getElementById('gwent-leader-modal')?.remove(); }
function openGwentLeaderModal() {
  const data = currentGwentData;
  if (!data) return;
  closeGwentLeaderModal();
  const leaderId = String(data.leader_id || '');
  const leaderName = String(data.leader_name || 'Líder');
  const faction = String(data.faction || 'Sua facção');
  const description = String(data.leader_description || 'Habilidade especial do líder.');
  const simple = gwentLeaderSimpleExplanation(leaderId, description);
  const mine = data.score?.[String(data.your_id)] || {};
  const canActivate = data.status === 'active' && data.phase === 'battle' && !!data.is_your_turn && !mine.passed && !data.leader_used;
  const needsRow = GWENT_LEADER_ROW_CHOICES.has(leaderId);
  const fixedRow = leaderId === 'oraculo_tempestade' ? 'ranged' : 'melee';
  const rowOptions = [['melee','Corpo a corpo'],['ranged','Longa distância'],['siege','Cerco']]
    .map(([value,label]) => `<option value="${value}" ${value === fixedRow ? 'selected' : ''}>${label}</option>`).join('');
  const status = data.leader_used ? 'HABILIDADE JÁ UTILIZADA' : canActivate ? 'PRONTO PARA ATIVAR' : 'DISPONÍVEL NA SUA VEZ';
  const modal = document.createElement('div');
  modal.id = 'gwent-leader-modal';
  modal.className = 'gwent-leader-modal';
  modal.setAttribute('role','dialog');
  modal.setAttribute('aria-modal','true');
  modal.setAttribute('aria-label',`Líder ${leaderName}`);
  modal.innerHTML = `<section class="gwent-leader-dialog">
    <button type="button" class="gwent-leader-close" data-leader-close aria-label="Fechar">×</button>
    <div class="gwent-leader-art"><span class="gwent-leader-portrait">${gwentLeaderArtMarkup(leaderId, 'gwent-leader-modal-image')}<i hidden>${gwentLeaderIcon(leaderId)}</i></span><small>${escapeHTML(faction)}</small></div>
    <div class="gwent-leader-details"><small class="eyebrow">CARTA DE LÍDER</small><h2>${escapeHTML(leaderName)}</h2>
      <span class="gwent-leader-state ${data.leader_used ? 'spent' : canActivate ? 'ready' : ''}">${status}</span>
      <section class="gwent-leader-ability"><small>HABILIDADE</small><p>${escapeHTML(description)}</p></section>
      <section class="gwent-leader-simple"><small>EXPLICANDO DE UM JEITO SIMPLES</small><p>${escapeHTML(simple)}</p></section>
      ${needsRow ? `<label class="gwent-leader-row"><span>ESCOLHA A FILEIRA</span><select data-leader-row ${canActivate ? '' : 'disabled'}>${rowOptions}</select></label>` : `<p class="gwent-leader-fixed-row">${leaderId === 'comandante_fornalha' ? 'A habilidade sempre afeta Corpo a Corpo.' : leaderId === 'oraculo_tempestade' ? 'A habilidade sempre afeta Longa Distância.' : 'Esta habilidade não precisa escolher uma fileira.'}</p>`}
      <button type="button" class="gwent-leader-confirm" data-leader-confirm ${canActivate ? '' : 'disabled'}>${data.leader_used ? 'HABILIDADE JÁ UTILIZADA' : 'ATIVAR HABILIDADE'}</button>
    </div></section>`;
  document.body.appendChild(modal);
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('[data-leader-close]')) { closeGwentLeaderModal(); return; }
    const confirm = event.target.closest('[data-leader-confirm]');
    if (!confirm || confirm.disabled) return;
    const row = modal.querySelector('[data-leader-row]')?.value || fixedRow;
    closeGwentLeaderModal();
    sendGwentAction('leader', '', row);
  });
  modal.querySelector('[data-leader-close]')?.focus();
}

const GWENT_IDENTITY_GUIDE = {
  chefe_guardiao_cinzas: {
    simple: 'Quando entra, fortalece em +1 um aliado que já esteja na mesma fileira. Se houver esse aliado, esta própria carta também ganha +1.',
    example: 'Exemplo: já existe um aliado em Corpo a Corpo. Ao jogar esta carta nessa fileira, o aliado ganha +1 e a nova carta também ganha +1. Se a fileira estiver vazia, nenhum desses bônus é aplicado.'
  },
  chefe_dama_vazio: {
    simple: 'A unidade inimiga mais forte perde 2 pontos de bônus. Ela não pode ficar com menos de -2 de bônus.',
    example: 'Exemplo: o inimigo mais forte tem +3 de bônus. Ele passa a ter +1. Se já tinha -2, não perde mais nada.'
  },
  chefe_rei_afogado: {
    simple: 'Esta carta ganha +2 se você já tiver alguma unidade no descarte. Se não tiver, ganha +1 quando o adversário tiver mais unidades em campo que você.',
    example: 'Exemplo: há uma unidade no seu descarte, então a carta recebe +2. Se seu descarte estiver vazio, ela só ganha +1 caso o adversário tenha mais unidades no campo.'
  },
  chefe_oraculo_ruina: {
    simple: 'A unidade inimiga mais forte perde 1 ponto de bônus. Esta carta também ganha +1 se o adversário estiver vencendo em pontos.',
    example: 'Exemplo: o inimigo mais forte tem +2 de bônus e cai para +1. Se o adversário ainda estiver na frente no placar, esta carta também recebe +1.'
  },
  arma_duas_luas: {
    simple: 'Esta carta ganha +1 se você tiver pelo menos outro aliado em uma fileira diferente da escolhida para ela.',
    example: 'Exemplo: você já tem uma unidade em Corpo a Corpo e joga esta carta em Cerco. Como há um aliado em outra fileira, ela recebe +1.'
  },
  arma_grande_sino: {
    simple: 'Esta carta ganha +2 quando sua pontuação total está menor que a do adversário.',
    example: 'Exemplo: você tem 12 pontos e o adversário tem 16. A carta recebe +2. Se você empatar ou ficar na frente, não recebe esse bônus.'
  },
  magia_selo_vigilia: {
    simple: 'Esta carta sofre 1 ponto a menos da penalidade do clima. Além disso, fortalece em +1 o primeiro aliado que já estiver na mesma fileira.',
    example: 'Exemplo: a fileira está sob chuva que tira 1 ponto. Esta carta ignora essa perda. Se já houver um aliado na fileira, ele recebe +1 de bônus.'
  },
  magia_trovao_oco: {
    simple: 'Todas as unidades inimigas na mesma fileira perdem 1 ponto de bônus. O bônus de cada uma não pode ficar abaixo de -2.',
    example: 'Exemplo: há três inimigos na fileira. Um tem +2 e cai para +1; outro tem +1 e fica com 0; o terceiro já está em -2 e não muda.'
  },
  magia_nevoa_antiga: {
    simple: 'Esta carta ganha +2 se houver chuva ou outro efeito climático ativo em qualquer fileira.',
    example: 'Exemplo: existe chuva em Cerco. Mesmo que esta carta seja jogada em Corpo a Corpo, ela recebe +2.'
  },
  magia_sol_negro: {
    simple: 'Esta carta ganha +2 se pelo menos uma unidade inimiga tiver bônus positivo.',
    example: 'Exemplo: uma unidade inimiga tem +1 de bônus. A condição já foi cumprida e esta carta recebe +2.'
  },
  covenant_lua_velada: {
    simple: 'Esta carta ganha +1. Depois, o aliado mais fraco que estiver em outra fileira também recebe +1 de bônus.',
    example: 'Exemplo: você joga esta carta em Longa Distância. Um aliado mais fraco está em Corpo a Corpo; ele recebe +1 e esta carta também recebe +1.'
  },
  chefe_malenia_lamina_miquella: {
    simple: 'Todos os inimigos da fileira escolhida recebem Podridão Escarlate. Quem já tinha uma marca recebe a segunda, que também corrói 1 ponto de bônus positivo.',
    example: 'Exemplo: há três inimigos em Cerco. Todos recebem Podridão. Um deles já estava marcado, então completa a segunda marca e perde 1 de bônus positivo, se tiver.'
  },
  chefe_radahn_flagelo_estrelas: {
    simple: 'O inimigo mais forte do campo é puxado para a fileira escolhida e perde 2 pontos de bônus.',
    example: 'Exemplo: a unidade inimiga mais forte está em Longa Distância. Você joga Radahn em Cerco: essa unidade é movida para Cerco e perde 2 de bônus.'
  },
  chefe_maliketh_morte_destinada: {
    simple: 'A unidade inimiga mais forte perde até 2 pontos de bônus. O bônus dela não pode ficar abaixo de -2.',
    example: 'Exemplo: o inimigo mais forte tem +3 de bônus e passa a ter +1. Se tinha +1, passa a -1.'
  },
  chefe_messmer_impalador: {
    simple: 'Todos os inimigos da fileira escolhida recebem Sangramento. Se alguém já tinha uma marca, a segunda causa Hemorragia e tira 2 pontos de bônus.',
    example: 'Exemplo: dois inimigos estão em Corpo a Corpo. Os dois recebem Sangramento. Se um já estava marcado, sofre Hemorragia e perde 2 de bônus.'
  },
  chefe_placidusax_lorde_dragao: {
    simple: 'Todos os inimigos da fileira escolhida recebem Geada. Esta carta ganha +1 para cada inimigo atingido, até no máximo +3.',
    example: 'Exemplo: há dois inimigos em Cerco. Os dois recebem Geada e Placidusax ganha +2. Com quatro inimigos, o bônus continua limitado a +3.'
  },
  gwent_v75_ordem_veterano_juramento: {
    simple: 'Esta carta entra com +1 de bônus. Se já houver um aliado na mesma fileira, o aliado mais fraco também recebe +1.',
    example: 'Exemplo: há dois aliados em Corpo a Corpo. Ao jogar o Veterano nessa fileira, ele ganha +1 e o aliado mais fraco também ganha +1.'
  },
  gwent_v75_ordem_confessora_graca: {
    simple: 'Limpa efeitos negativos de até dois aliados da mesma fileira e dá +1 de bônus a cada um. Se ninguém precisar ser limpo, fortalece o aliado mais fraco em +1. Se não houver aliado, esta carta ganha +1.',
    example: 'Exemplo: dois aliados em Cerco estão com Geada e Sangramento. A Confessora remove esses efeitos e cada um recebe +1. Se ninguém estiver afetado, ela fortalece o aliado mais fraco.'
  },
  gwent_v75_veu_acolito_sangue: {
    simple: 'O inimigo mais forte da fileira escolhida recebe Sangramento. Se já tinha uma marca, sofre Hemorragia, perde 2 de bônus e esta carta ganha +1.',
    example: 'Exemplo: o inimigo mais forte em Longa Distância já tem Sangramento. O Acólito completa a segunda marca, tira 2 de bônus desse inimigo e ganha +1.'
  },
  gwent_v75_veu_carrasco_preco: {
    simple: 'Sacrifica seu aliado mais fraco da mesma fileira e recebe bônus igual ao poder efetivo dele, até +3. Se não houver aliado, recebe +1.',
    example: 'Exemplo: há um aliado com 2 de poder efetivo na fileira. Ele é sacrificado e o Carrasco ganha +2 de bônus. O ganho nunca passa de +3.'
  },
  gwent_v75_lua_oraculo_geada: {
    simple: 'O inimigo mais forte da fileira escolhida recebe Geada. Se ele já tinha uma marca de Geada, esta carta também ganha +1.',
    example: 'Exemplo: o inimigo mais forte em Cerco já tem uma marca de Geada. O Oráculo completa a segunda e recebe +1.'
  },
  gwent_v75_lua_graviturgista: {
    simple: 'Até dois inimigos da fileira escolhida que tenham bônus positivo perdem 1 ponto de bônus. Se atingir dois, esta carta ganha +1.',
    example: 'Exemplo: dois inimigos em Cerco têm +2 e +1 de bônus. Os dois perdem 1; como foram atingidos dois inimigos, o Graviturgista recebe +1.'
  }
};

function gwentSimpleExplanation(card) {
  const identityGuide = card?.habilidade_identidade ? GWENT_IDENTITY_GUIDE[String(card.id || '')] : null;
  if (identityGuide?.simple) return identityGuide.simple;
  const skill = String(card?.habilidade || '');
  const explanations = {
    devoto: 'Quando esta carta entra, ela ganha +1 de poder se você já tiver pelo menos duas unidades da mesma facção no campo.',
    gloria: 'Se você vencer a rodada com esta unidade no campo, ela permanece para a próxima rodada. Se perder, ela vai para o descarte normalmente.',
    legado: 'Se você venceu a rodada anterior, esta unidade entra na próxima rodada com +2 de poder.',
    sinergia_faccao: 'Quando esta carta entra, ela ganha +1 de poder para cada unidade aliada da mesma facção que já estiver no campo.',
    primeira_luz: 'Se esta unidade entrar na primeira rodada, ela ganha +1 de poder.',
    retaliacao: 'Se sua pontuação estiver menor que a do adversário, esta unidade ganha +1 de poder.',
    impeto: 'Se sua pontuação estiver maior que a do adversário, esta unidade ganha +1 de poder.',
    ultimo_folego: 'Se esta unidade entrar na terceira rodada, ela ganha +1 de poder.',
    contragolpe: 'Quando você estiver perdendo em pontos, esta unidade ganha +2 de poder.',
    encadeamento: 'Se sua última unidade foi colocada nesta mesma fileira, esta unidade ganha +2.',
    adaptacao: 'Se sua última unidade foi colocada em outra fileira, esta unidade ganha +1.',
    sangue_frio: 'Se os dois jogadores estiverem empatados em pontos, esta unidade ganha +2.',
    instinto: 'Quando você estiver perdendo em pontos, esta unidade ganha +2.',
    precisao: 'Quando esta unidade entra em Longa Distância, ela ganha +1.',
    drenagem: 'Todas as unidades inimigas perdem 1 ponto de bônus, até o limite de -2.',
    cacador_arcano: 'Esta unidade ganha +1 se o inimigo tiver uma unidade da Lua Negra ou alguma unidade fortalecida.',
    quebra_ritmo: 'Esta unidade ganha +1 se o adversário jogou sua última unidade nesta mesma fileira.',
    lei_primeva: 'Na primeira rodada, esta unidade entra 2 pontos mais forte.',
    decreto_soberano: 'Todas as unidades inimigas perdem 2 pontos de bônus. A redução não passa do limite de -2.',
    olho_tempestade: 'Quando a fileira desta unidade está com clima ativo, ela ganha +2 de poder.',
    fome_abismo: 'Quando sua pontuação total está menor que a do adversário, esta unidade ganha +2 de poder.',
    paradoxo_eterno: 'Na terceira rodada, esta unidade ganha +2 se o adversário venceu a segunda rodada.',
    guardiao_fileira: 'Para cada outra unidade sua na mesma fileira, esta carta ganha +1, até ganhar +3.',
    cacador_solitario: 'Se esta for a única unidade sua na fileira, ela ganha +2.',
    estandarte: 'Quando entra, fortalece em +1 as outras unidades suas que estão na mesma fileira.',
    resistencia_climatica: 'Ignora até 2 pontos da fraqueza causada pelo clima. Se entrar sem clima ativo, ganha +1.',
    eco_arcano: 'Se você já tiver uma carta especial no descarte, esta unidade ganha +2.',
    vinganca: 'Quando esta unidade for destruída, suas outras unidades na mesma fileira ganham +1.',
    escudo_ferro: 'Esta unidade entra protegida por um Escudo. O Escudo pode impedir a primeira tentativa de removê-la.',
    ressurgir: 'Se houver uma unidade elegível no descarte, traz a mais forte com poder-base 5 ou menos de volta ao campo.',
    devorar: 'Ao entrar, esta unidade consome sua unidade mais fraca na mesma fileira e recebe parte da força dela, até +4.',
    sobrevivente: 'Se você vencer a rodada com esta unidade em campo, ela permanece para a próxima rodada.',
    espolios: 'Se você vencer a rodada com esta unidade em campo, compra mais uma carta.',
    gwent_egide: 'Escolha uma unidade sua para receber Escudo e ficar protegida contra uma tentativa de remoção.',
    gwent_requiem: 'Traz do descarte uma unidade com poder-base 6 ou menos diretamente para o campo.',
    gwent_passo: 'Escolha uma unidade sua e uma fileira de destino. A carta muda essa unidade de lugar.',
    dupla_fornalha: 'Se houver outra unidade sua na mesma fileira, esta carta ganha +2.',
    irmandade_veu: 'Se houver outra unidade sua em uma fileira diferente, esta carta ganha +2.',
    circulo_arcano: 'Esta carta ganha +2 se você tiver outra unidade na mesma fileira ou uma carta especial no descarte.',
    gwent_clima: 'Escolha uma fileira. A chuva enfraquece em 1 ponto todas as unidades dos dois lados que estiverem nela enquanto o clima durar.',
    gwent_nevoa: 'Escolha uma fileira inimiga. Todas as unidades dela recebem uma marca de Podridão, que reduz seu poder. Cartas de raridade Lendária ou maior aplicam uma segunda marca.',
    gwent_geada: 'Todas as unidades inimigas recebem uma marca de Geada, que reduz seu poder. Raridades Lendárias ou maiores aplicam uma segunda marca.',
    gwent_chuva: 'As unidades inimigas na fileira de Cerco recebem Sangramento. Quando uma unidade junta duas marcas, perde 2 pontos de bônus.',
    gwent_chifre: 'Escolha uma das suas fileiras. Suas unidades nela recebem +2 de bônus.',
    gwent_medico: 'Escolhe uma unidade permitida do seu descarte e devolve essa carta para sua mão.',
    gwent_queima: 'Tenta destruir a unidade mais forte de cada jogador. Um Escudo pode impedir a destruição.',
    gwent_purificar: 'Remove o clima ativo de todas as fileiras.',
    gwent_execucao: 'Escolha uma fileira inimiga. Pode destruir uma unidade com até 6 de poder efetivo. Escudo pode impedir.',
    gwent_vinculo: 'Se você tiver pelo menos duas unidades na fileira escolhida, todas elas recebem +2 de bônus.',
    gwent_batedor: 'Compra uma carta da sua reserva, caso ainda exista alguma.',
    gwent_muralha: 'Escolha uma fileira. Suas unidades nela recebem +1 de bônus.',
    gwent_sangramento: 'Marca as unidades inimigas da fileira escolhida. A segunda marca causa Hemorragia e reduz 2 de bônus.',
    gwent_geada_cariana: 'Escolha uma fileira inimiga. As unidades nela recebem marcas de Geada, que diminuem seu poder.',
    gwent_podrida: 'Escolha uma fileira inimiga. As marcas de Podridão diminuem o poder e podem corroer bônus positivos.',
    gwent_loucura: 'Escolha uma fileira inimiga. As marcas de Loucura diminuem o poder e podem apagar bônus positivos.',
    gwent_chama: 'Remove Geada das suas unidades. Cada unidade limpa recebe +1 de poder.',
    gwent_invocacao: 'Escolha uma fileira e invoque Lobos Espirituais nela.',
    reliquia_godrick: 'Você precisa ter pelo menos uma unidade sua no campo. Todas as suas unidades recebem +1 de bônus.',
    reliquia_renala: 'Remove Geada e Podridão das suas unidades afetadas. Cada uma que for limpa recebe +1 de bônus.',
    reliquia_morte: 'Em cada fileira, reduz até 2 pontos do bônus positivo da unidade inimiga que tiver o maior bônus.',
    reliquia_noite_chama: 'Escolha uma fileira e uma postura. A Noite aplica Geada a todos os inimigos dela; a Chama atinge o inimigo mais forte.',
    reliquia_lamina_negra: 'Escolha uma fileira e uma unidade inimiga. Reduz o bônus dela em 3. Escudo bloqueia o golpe.',
    reliquia_algemas: 'Escolha uma fileira e uma unidade inimiga. Remove o bônus positivo dela. Escudo não é removido.'
  };
  return explanations[skill] || String(card?.habilidade_texto || 'Esta carta ativa o efeito especial descrito em Habilidade. Leia a condição e escolha a fileira ou o alvo quando a tela pedir.');
}

function closeGwentCardPreview() {
  document.querySelectorAll('.gwent-row.is-card-preview, .gwent-board-card.is-card-preview, .gwent-board-side.is-card-preview').forEach(el => el.classList.remove('is-card-preview'));
}
function updateGwentCardPreview(card, row, previewNode) {
  closeGwentCardPreview();
  if (!card || !currentGwentData || !previewNode) return;
  const skill = String(card.habilidade || '');
  const score = currentGwentData.score || {};
  const mine = score[String(currentGwentData.your_id)] || {};
  const enemyKey = Object.keys(score).find(id => String(id) !== String(currentGwentData.your_id));
  const enemy = score[enemyKey] || {};
  let rowKey = row || 'melee';
  if (skill === 'gwent_chuva') rowKey = 'siege';

  let targets = [];
  let affectedSides = [];
  let allRows = false;
  let message = '';
  const identityExtraRows = new Map();
  const markIdentityRow = (side, rowName) => {
    if (!rowName) return;
    if (!identityExtraRows.has(side)) identityExtraRows.set(side, new Set());
    identityExtraRows.get(side).add(rowName);
  };
  const ownRows = new Set(['gwent_chifre','gwent_vinculo','gwent_muralha','gwent_invocacao']);
  const enemyAll = new Set(['gwent_geada','drenagem','decreto_soberano']);
  const enemyPicked = new Set(['gwent_nevoa','gwent_geada_cariana','gwent_podrida','gwent_loucura','gwent_sangramento']);
  const bothPicked = new Set(['gwent_clima']);

  // For selectable targets, use the exact eligible list returned by the backend.
  // This keeps the preview aligned with server rules for shields, rarity and power limits.
  const serverTargets = gwentOpcoesDoAlvo(String(card.id), rowKey);
  if (serverTargets && ['gwent_execucao','gwent_passo','gwent_egide'].includes(skill)) {
    const side = skill === 'gwent_execucao' ? 'enemy' : 'mine';
    const sideData = side === 'mine' ? mine : enemy;
    targets = serverTargets.opcoes || [];
    affectedSides = [[side, sideData]];
    if (skill === 'gwent_execucao') message = `Prévia: ${targets.length} unidade(s) inimiga(s) elegíveis em ${gwentRowLabel(rowKey)} podem ser atingidas. O Escudo ainda pode bloquear a remoção.`;
    else if (skill === 'gwent_passo') message = `Prévia: ${targets.length} unidade(s) sua(s) podem ser movidas para ${gwentRowLabel(rowKey)}.`;
    else message = `Prévia: ${targets.length} unidade(s) sua(s) podem receber Escudo.`;
  } else if (card?.habilidade_identidade) {
    // Habilidades individuais são identificadas pelo ID real da carta no motor.
    // A prévia usa o mesmo conjunto de alvos do efeito correspondente.
    const id = String(card.id || '');
    const ownBoard = Array.isArray(mine.board) ? mine.board : [];
    const enemyBoard = Array.isArray(enemy.board) ? enemy.board : [];
    const powerOf = unit => gwentEffectivePower(unit, gwentWeatherSnapshot(currentGwentData)[unit.row] || 0);
    const weakest = units => units.slice().sort((a,b) => powerOf(a) - powerOf(b))[0] || null;
    const strongest = units => units.slice().sort((a,b) => powerOf(b) - powerOf(a))[0] || null;
    const ownRow = ownBoard.filter(unit => unit.row === rowKey);
    const enemyRow = enemyBoard.filter(unit => unit.row === rowKey);
    if (['chefe_dama_vazio','chefe_oraculo_ruina','chefe_maliketh_morte_destinada'].includes(id)) {
      targets = [strongest(enemyBoard)].filter(Boolean); affectedSides = [['enemy', enemy]];
      message = `Prévia: a unidade inimiga mais forte no campo será afetada fora da fileira escolhida.`;
    } else if (id === 'chefe_guardiao_cinzas') {
      targets = [ownRow[0]].filter(Boolean); affectedSides = [['mine', mine]]; markIdentityRow('mine', rowKey);
      message = targets.length ? `Prévia: o primeiro aliado seu em ${gwentRowLabel(rowKey)} recebe +1; a carta também recebe +1.` : 'Prévia: sem aliado na fileira escolhida, o bônus desta habilidade não será ativado.';
    } else if (id === 'chefe_rei_afogado') {
      message = 'Prévia: a carta ganha +2 se você tiver carta no descarte; sem descarte, ganha +1 se o adversário tiver mais unidades em campo.';
    } else if (id === 'arma_duas_luas') {
      message = 'Prévia: a carta ganha +1 se você já tiver um aliado em outra fileira.';
    } else if (id === 'arma_grande_sino') {
      message = 'Prévia: a carta ganha +2 se sua pontuação total estiver abaixo da pontuação adversária.';
    } else if (id === 'magia_selo_vigilia') {
      targets = [ownRow[0]].filter(Boolean); affectedSides = [['mine', mine]]; markIdentityRow('mine', rowKey);
      message = 'Prévia: a carta reduz em 1 a penalidade de clima que sofre; o primeiro aliado já presente na fileira recebe +1.';
    } else if (id === 'magia_trovao_oco') {
      targets = enemyRow; affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      message = `Prévia: ${targets.length} inimigo(s) em ${gwentRowLabel(rowKey)} perde(m) 1 de bônus.`;
    } else if (id === 'magia_nevoa_antiga') {
      message = 'Prévia: a carta ganha +2 se houver clima ativo em qualquer fileira.';
    } else if (id === 'magia_sol_negro') {
      message = 'Prévia: a carta ganha +2 se algum inimigo tiver bônus positivo.';
    } else if (id === 'covenant_lua_velada') {
      targets = [weakest(ownBoard.filter(unit => unit.row !== rowKey))].filter(Boolean); affectedSides = [['mine', mine]];
      message = targets.length ? 'Prévia: a carta ganha +1 e o aliado mais fraco em outra fileira recebe +1.' : 'Prévia: a carta ganha +1; não há aliado em outra fileira para receber o segundo bônus.';
    } else if (['chefe_malenia_lamina_miquella','chefe_messmer_impalador','chefe_placidusax_lorde_dragao'].includes(id)) {
      targets = enemyRow; affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      const effectLabel = id === 'chefe_malenia_lamina_miquella' ? 'Podridão Escarlate' : id === 'chefe_messmer_impalador' ? 'Sangramento' : 'Geada';
      message = `Prévia: ${targets.length} inimigo(s) em ${gwentRowLabel(rowKey)} receberá(ão) ${effectLabel}.`;
    } else if (id === 'chefe_radahn_flagelo_estrelas') {
      targets = [strongest(enemyBoard)].filter(Boolean); affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      message = 'Prévia: o inimigo mais forte será movido para a fileira escolhida e perderá 2 de bônus.';
    } else if (id === 'gwent_v75_ordem_veterano_juramento') {
      targets = [weakest(ownRow)].filter(Boolean); affectedSides = [['mine', mine]]; markIdentityRow('mine', rowKey);
      message = 'Prévia: a carta ganha +1; se houver aliado na fileira, o mais fraco também ganha +1.';
    } else if (id === 'gwent_v75_ordem_confessora_graca') {
      const statusKeys = ['sangramento','geada','podrida','loucura'];
      const marked = ownRow.filter(unit => statusKeys.some(key => Number(unit[key] || 0) > 0));
      targets = marked.length ? marked.slice().sort((a,b) => powerOf(a)-powerOf(b)).slice(0,2) : [weakest(ownRow)].filter(Boolean);
      affectedSides = [['mine', mine]]; markIdentityRow('mine', rowKey);
      message = marked.length ? `Prévia: até ${targets.length} aliado(s) em ${gwentRowLabel(rowKey)} serão purificados e receberão +1.` : (targets.length ? 'Prévia: nenhum aliado precisa de purificação; o aliado mais fraco recebe +1.' : 'Prévia: sem aliados nessa fileira, a própria carta recebe +1.');
    } else if (id === 'gwent_v75_veu_acolito_sangue') {
      targets = [strongest(enemyRow)].filter(Boolean); affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      message = targets.length ? 'Prévia: o inimigo mais forte da fileira recebe Sangramento; a segunda marca causa Hemorragia.' : 'Prévia: não há inimigo nessa fileira para receber Sangramento.';
    } else if (id === 'gwent_v75_veu_carrasco_preco') {
      targets = [weakest(ownRow)].filter(Boolean); affectedSides = [['mine', mine]]; markIdentityRow('mine', rowKey);
      message = targets.length ? 'Prévia: o aliado mais fraco da fileira será sacrificado para fortalecer esta carta (até +3).' : 'Prévia: sem aliado nessa fileira, esta carta recebe +1.';
    } else if (id === 'gwent_v75_lua_oraculo_geada') {
      targets = [strongest(enemyRow)].filter(Boolean); affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      message = targets.length ? 'Prévia: o inimigo mais forte recebe Geada; se já estiver marcado, esta carta ganha +1.' : 'Prévia: não há inimigo nessa fileira para receber Geada.';
    } else if (id === 'gwent_v75_lua_graviturgista') {
      targets = enemyRow.filter(unit => Number(unit.bonus || 0) > 0).sort((a,b) => Number(b.bonus || 0) - Number(a.bonus || 0)).slice(0,2);
      affectedSides = [['enemy', enemy]]; markIdentityRow('enemy', rowKey);
      message = `Prévia: ${targets.length} inimigo(s) com bônus positivo em ${gwentRowLabel(rowKey)} perderá(ão) 1 de bônus.`;
    } else {
      message = 'Prévia: esta unidade tem uma habilidade exclusiva; consulte a explicação detalhada antes de jogar.';
    }
  } else {
    if (enemyAll.has(skill)) {
      affectedSides = [['enemy', enemy]];
      targets = [...(enemy.board || [])];
      allRows = true;
    } else if (enemyPicked.has(skill)) {
      affectedSides = [['enemy', enemy]];
      targets = (enemy.board || []).filter(unit => unit.row === rowKey);
    } else if (bothPicked.has(skill)) {
      affectedSides = [['mine', mine],['enemy', enemy]];
      targets = [...(mine.board || []), ...(enemy.board || [])].filter(unit => unit.row === rowKey);
    } else if (skill === 'gwent_chuva') {
      affectedSides = [['enemy', enemy]];
      targets = (enemy.board || []).filter(unit => unit.row === 'siege');
    } else if (ownRows.has(skill)) {
      affectedSides = [['mine', mine]];
      targets = (mine.board || []).filter(unit => unit.row === rowKey);
    } else if (skill === 'gwent_chama') {
      affectedSides = [['mine', mine]];
      targets = (mine.board || []).filter(unit => Number(unit.geada || 0) > 0);
    } else if (skill === 'reliquia_renala') {
      affectedSides = [['mine', mine]];
      targets = (mine.board || []).filter(unit => Number(unit.geada || 0) > 0 || Number(unit.podrida || 0) > 0);
    } else if (skill === 'gwent_purificar') {
      affectedSides = [['mine', mine],['enemy', enemy]];
      allRows = true;
    } else if (skill === 'gwent_queima') {
      const highest = side => (side.board || []).slice().sort((a,b) => gwentEffectivePower(b)-gwentEffectivePower(a))[0];
      targets = [highest(mine), highest(enemy)].filter(Boolean);
      affectedSides = [['mine',mine],['enemy',enemy]];
    } else if (skill === 'reliquia_morte') {
      affectedSides = [['enemy', enemy]];
      targets = ['melee','ranged','siege'].map(rowName => (enemy.board || [])
        .filter(unit => unit.row === rowName)
        .sort((a,b) => Number(b.bonus || 0) - Number(a.bonus || 0))[0]).filter(Boolean);
      allRows = true;
    }
  }

  const rowsToHighlight = new Map();
  for (const [side, sideData] of affectedSides) {
    const rows = new Set(targets
      .filter(unit => (sideData.board || []).some(candidate => String(candidate.id) === String(unit.id)))
      .map(unit => unit.row));
    if (allRows || skill === 'gwent_geada' || skill === 'gwent_purificar' || skill === 'reliquia_morte') {
      for (const [key] of gwentRows) rows.add(key);
    }
    if (skill === 'gwent_clima' || skill === 'gwent_invocacao' || skill === 'gwent_execucao' || enemyPicked.has(skill) || ownRows.has(skill) || skill === 'gwent_chuva') rows.add(rowKey);
    if (skill === 'gwent_passo') rows.add(rowKey);
    rowsToHighlight.set(side, [...rows].filter(Boolean));
  }
  for (const [side, extraRows] of identityExtraRows) {
    const rows = rowsToHighlight.get(side) || [];
    rowsToHighlight.set(side, [...new Set([...rows, ...extraRows])]);
  }
  for (const [side, rows] of rowsToHighlight) {
    const sideSelector = side === 'mine' ? '.gwent-board-mine' : '.gwent-board-enemy';
    const sideNode = document.querySelector(`#gwent-arena ${sideSelector}`);
    sideNode?.classList.add('is-card-preview');
    for (const targetRow of rows) sideNode?.querySelector(`.gwent-row[data-row="${CSS.escape(targetRow)}"]`)?.classList.add('is-card-preview');
  }
  for (const unit of targets) {
    document.querySelector(`#gwent-arena .gwent-board-card[data-card-id="${CSS.escape(String(unit.id))}"]`)?.classList.add('is-card-preview');
  }

  const rowName = gwentRowLabel(rowKey);
  if (message) previewNode.textContent = message;
  else if (skill === 'gwent_clima') previewNode.textContent = `Prévia: ${targets.length} unidade(s) dos dois lados em ${rowName} sofrerão a penalidade da chuva.`;
  else if (skill === 'gwent_geada') previewNode.textContent = `Prévia: ${targets.length} unidade(s) inimiga(s) em todas as fileiras receberão Geada.`;
  else if (skill === 'gwent_purificar') previewNode.textContent = 'Prévia: o clima será removido das três fileiras para os dois jogadores.';
  else if (skill === 'gwent_invocacao') previewNode.textContent = `Prévia: Lobos Espirituais serão invocados em ${rowName}.`;
  else if (skill === 'gwent_batedor') previewNode.textContent = 'Prévia: você comprará carta(s) da sua reserva, se ainda houver.';
  else if (skill === 'gwent_medico' || skill === 'gwent_requiem') previewNode.textContent = 'Prévia: a escolha será feita entre unidades elegíveis do seu descarte.';
  else if (!affectedSides.length) previewNode.textContent = 'Prévia: confira as unidades e a fileira destacadas. O servidor valida a jogada antes de aplicá-la.';
  else previewNode.textContent = `Prévia: ${targets.length} unidade(s) em ${rowName} no ${affectedSides.map(([side]) => side === 'mine' ? 'seu campo' : 'campo inimigo').join(' e ')} serão afetadas.`;
}
function gwentSimpleExample(card) {
  const identityGuide = card?.habilidade_identidade ? GWENT_IDENTITY_GUIDE[String(card.id || '')] : null;
  if (identityGuide?.example) return identityGuide.example;
  const skill = String(card?.habilidade || '');
  const examples = {
    devoto: 'Exemplo: você já tem duas unidades dos Esquecidos no campo e joga outra carta dos Esquecidos com Devoto. Ela recebe +1. Com apenas uma aliada da mesma facção, não recebe o bônus.',
    gloria: 'Exemplo: o Anjo Esquecido está no campo e você vence a rodada. Ele permanece para a próxima. Se a NARA vencer, ele vai para o descarte.',
    legado: 'Exemplo: você vence a primeira rodada. Ao jogar o Missionário Esquecido na segunda, ele entra com +2 de poder. Se você perdeu a rodada anterior, esse bônus não ativa.',
    sinergia_faccao: 'Exemplo: você tem três unidades dos Esquecidos no campo e joga o Cruzado Esquecido. Ele ganha +3 de poder, porque já havia três aliados da mesma facção.',
    lei_primeva: 'Exemplo: se jogar esta unidade na primeira rodada, ela recebe +2. Se jogar nas rodadas seguintes, esse bônus especial não acontece.',
    decreto_soberano: 'Exemplo: um inimigo com +3 de bônus passa a ter +1; outro com +1 passa a ter -1. A habilidade não reduz ninguém abaixo de -2 de bônus.',
    olho_tempestade: 'Exemplo: se a fileira onde esta unidade está tiver chuva, ela recebe +2. Sem clima naquela fileira, não recebe esse bônus.',
    fome_abismo: 'Exemplo: se você tem 18 pontos e a NARA tem 22, a unidade recebe +2. Se você estiver empatando ou vencendo, não recebe esse bônus.',
    paradoxo_eterno: 'Exemplo: se a NARA venceu a segunda rodada, esta unidade recebe +2 quando entrar na terceira.',
    guardiao_fileira: 'Exemplo: com três outras unidades suas na mesma fileira, esta carta pode receber +3 no máximo.',
    cacador_solitario: 'Exemplo: se esta unidade estiver sozinha na fileira, recebe +2. Se você colocar outra ali, perde a condição de solitária.',
    estandarte: 'Exemplo: se você tiver outras duas unidades na fileira, as duas recebem +1 quando o Estandarte entrar.',
    resistencia_climatica: 'Exemplo: sob chuva de nível 2, esta unidade ignora até 2 pontos da penalidade. Se entrar em uma fileira sem clima, recebe +1.',
    eco_arcano: 'Exemplo: depois que uma carta especial for para seu descarte, esta unidade recebe +2 quando a condição for verificada.',
    vinganca: 'Exemplo: se esta unidade for destruída, suas outras unidades que estiverem na mesma fileira recebem +1.',
    escudo_ferro: 'Exemplo: se um efeito tentar destruir esta unidade, o Escudo é consumido e ela continua no campo.',
    ressurgir: 'Exemplo: se houver no descarte uma unidade com poder-base 4 e outra com poder-base 5, a de poder 5 é a mais forte elegível e pode voltar.',
    devorar: 'Exemplo: se sua unidade mais fraca na fileira tiver poder efetivo 3, esta carta pode ganhar +3 de bônus ao consumi-la.',
    sobrevivente: 'Exemplo: se você ganhar a rodada com esta carta em campo, ela continua na arena quando a próxima rodada começar.',
    espolios: 'Exemplo: se você vencer a rodada e esta carta continuar no campo, compra uma carta da sua reserva.',
    gwent_egide: 'Exemplo: escolha uma unidade sua sem Escudo. Ela recebe proteção contra uma tentativa de remoção.',
    gwent_requiem: 'Exemplo: uma unidade no descarte com poder-base 5 pode voltar diretamente ao campo; uma com poder-base 7 não pode.',
    gwent_passo: 'Exemplo: escolha uma unidade sua de Corpo a Corpo e mande-a para Longa Distância.',
    dupla_fornalha: 'Exemplo: esta unidade ganha +2 se você já tiver outra unidade na mesma fileira.',
    irmandade_veu: 'Exemplo: se esta carta está em Corpo a Corpo e você tem outra unidade em Cerco, ela ganha +2.',
    circulo_arcano: 'Exemplo: uma unidade sua na mesma fileira ou uma carta especial no descarte já pode ativar o bônus +2.',
    primeira_luz: 'Exemplo: se esta carta entrar na primeira rodada com poder 4, passa a contar como 5. Na segunda rodada, esse bônus de entrada não acontece.',
    retaliacao: 'Exemplo: você tem 12 pontos e o adversário 16. Enquanto estiver perdendo, esta unidade recebe +1.',
    impeto: 'Exemplo: você tem 18 pontos e o adversário 14. Como está vencendo, esta unidade recebe +1.',
    ultimo_folego: 'Exemplo: ao jogar esta unidade na terceira rodada, ela recebe +1. Na primeira ou na segunda rodada, não recebe esse bônus.',
    contragolpe: 'Exemplo: você tem 10 pontos e o adversário 15. Esta unidade recebe +2 enquanto você estiver atrás.',
    encadeamento: 'Exemplo: sua última carta foi colocada em Cerco. Se jogar esta unidade também em Cerco, ela ganha +2.',
    adaptacao: 'Exemplo: sua última unidade foi para Corpo a Corpo. Ao colocar esta carta em Longa Distância, ela ganha +1.',
    sangue_frio: 'Exemplo: você e o adversário têm 17 pontos. Como o placar está empatado, esta unidade recebe +2.',
    instinto: 'Exemplo: você tem 9 pontos e o adversário 12. Enquanto estiver perdendo, esta unidade recebe +2.',
    precisao: 'Exemplo: esta unidade tem 4 de poder. Ao colocá-la em Longa Distância, passa a contar como 5.',
    drenagem: 'Exemplo: um inimigo tem +2 de bônus. A habilidade reduz esse bônus em 1. Os inimigos afetados não perdem além do limite de -2.',
    cacador_arcano: 'Exemplo: se a NARA tiver uma unidade da Lua Negra em campo, esta carta recebe +1. Uma unidade inimiga com bônus positivo também pode cumprir a condição.',
    quebra_ritmo: 'Exemplo: a NARA acabou de jogar uma unidade em Cerco. Se esta carta entrar em Cerco no seu turno, recebe +1.',
    gwent_batedor: 'Exemplo: se ainda houver cartas na sua reserva, esta habilidade compra uma. Em raridades mais altas, pode comprar uma segunda.',
    gwent_chama: 'Exemplo: se duas unidades suas estiverem com Geada, as duas são purificadas e recebem +1 de bônus cada.',
    gwent_execucao: 'Exemplo: escolha uma unidade inimiga com poder efetivo dentro do limite mostrado. A carta tenta removê-la; se ela tiver Escudo, poderá resistir.',
    gwent_geada_cariana: 'Exemplo: escolha uma fileira inimiga. As unidades nela recebem Geada; as primeiras podem receber uma marca extra conforme a raridade da carta.',
    gwent_invocacao: 'Exemplo: escolha Longa Distância. A carta coloca Lobos Espirituais nessa fileira para aumentar seu exército.',
    gwent_loucura: 'Exemplo: uma unidade inimiga recebe a segunda marca de Loucura. Além de perder poder efetivo, ela perde os bônus positivos que ainda tinha.',
    gwent_medico: 'Exemplo: uma unidade sua de poder-base 4 está no descarte. A habilidade pode devolvê-la para sua mão para você jogar depois.',
    gwent_podrida: 'Exemplo: a segunda marca de Podridão reduz o poder efetivo e também corrói 1 ponto de bônus positivo, se a unidade tiver algum.',
    gwent_purificar: 'Exemplo: se houver chuva em Cerco e outra condição climática em Longa Distância, esta carta limpa o clima das três fileiras.',
    gwent_sangramento: 'Exemplo: escolha uma fileira inimiga. Se uma unidade que já tinha Sangramento receber outra marca, sofre Hemorragia e perde 2 de bônus.',
    reliquia_algemas: 'Exemplo: um inimigo tem +3 de bônus. As Algemas removem esse bônus positivo; se ele tiver Escudo, o Escudo continua intacto.',
    reliquia_lamina_negra: 'Exemplo: escolha um inimigo na fileira selecionada. A Lâmina reduz seu bônus em 3; se houver Escudo, ele bloqueia o golpe.',
    reliquia_morte: 'Exemplo: em cada fileira, o inimigo com maior bônus positivo perde até 2 pontos desse bônus.',
    reliquia_noite_chama: 'Exemplo: escolha Cerco e a postura da Noite para aplicar Geada a todos os inimigos ali. Na postura da Chama, atinge o inimigo mais forte; o Escudo pode bloquear.',
    reliquia_renala: 'Exemplo: duas unidades suas estão com Geada ou Podridão. A Runa limpa esses efeitos e cada unidade purificada recebe +1 de bônus.',
    gwent_clima: 'Exemplo: escolha Longa Distância. Uma unidade sua com poder efetivo 5 e uma unidade inimiga com poder 4 passam a contar como 4 e 3 enquanto a chuva estiver ativa (sem cair abaixo de 1).',
    gwent_nevoa: 'Exemplo: se houver três unidades inimigas em Cerco, as três recebem Podridão e perdem poder efetivo. A tempestade não atinge suas próprias unidades.',
    gwent_geada: 'Exemplo: se o adversário tiver uma unidade em cada fileira, as três recebem Geada. A redução é aplicada ao poder efetivo.',
    gwent_chuva: 'Exemplo: cada inimigo em Cerco recebe uma marca de Sangramento. Quando uma unidade acumula a segunda marca, perde 2 pontos de bônus e as marcas são consumidas.',
    gwent_chifre: 'Exemplo: se você tiver duas unidades em Corpo a Corpo, ambas recebem +2 de bônus.',
    gwent_vinculo: 'Exemplo: escolha Cerco. Se você tiver pelo menos duas unidades nessa fileira, todas recebem +2 de bônus.',
    gwent_muralha: 'Exemplo: escolha Longa Distância. Todas as suas unidades nessa fileira recebem +1 de bônus.',
    reliquia_godrick: 'Exemplo: você tem três unidades no campo. Ao ativar a runa, as três recebem +1 de bônus. Sem nenhuma unidade aliada, a carta não pode ser usada.',
    gwent_queima: 'Exemplo: o jogo compara a unidade mais forte de cada lado e tenta remover as duas. Um Escudo pode bloquear a remoção da unidade protegida.'
  };
  return examples[skill] || 'Exemplo: observe a condição descrita na habilidade. Quando ela for cumprida, a carta aplica esse efeito à unidade, fileira ou jogador indicado. Se a jogada exigir um alvo, a tela permite escolhê-lo antes de confirmar.';
}

function gwentAnimateRemovedBoardCards(arena, nextIds, enabled = true) {
  if (!enabled || !arena) return;
  const next = nextIds instanceof Set ? nextIds : new Set(nextIds || []);
  for (const card of arena.querySelectorAll('.gwent-board-card[data-card-id]')) {
    if (next.has(String(card.dataset.cardId))) continue;
    const rect = card.getBoundingClientRect();
    if (!rect.width || !rect.height) continue;
    const ghost = card.cloneNode(true);
    ghost.classList.add('gwent-destroy-ghost');
    ghost.setAttribute('aria-hidden', 'true');
    ghost.removeAttribute('role');
    ghost.removeAttribute('tabindex');
    ghost.style.left = `${rect.left}px`;
    ghost.style.top = `${rect.top}px`;
    ghost.style.width = `${rect.width}px`;
    ghost.style.height = `${rect.height}px`;
    document.body.appendChild(ghost);
    window.setTimeout(() => ghost.remove(), 780);
  }
}

function closeGwentRelicPicker() { document.getElementById('gwent-relic-modal')?.remove(); }
function openGwentRelicPicker(data = currentGwentData) {
  if (!data || !data.is_your_turn || data.phase !== 'battle') return;
  const relicId = String(data.equipped_relic_id || '');
  if (!relicId || data.relic_used) return;
  const mine = data.score?.[String(data.your_id)] || {};
  const enemyId = String(data.opponent?.id || '');
  const enemy = data.score?.[enemyId] || {};
  const needsRow = ['reliquia_noite_chama','reliquia_lamina_negra','reliquia_algemas_margit'].includes(relicId);
  const needsTarget = ['reliquia_lamina_negra','reliquia_algemas_margit'].includes(relicId);
  const rowLabels = {melee:'Corpo a corpo',ranged:'Longa distância',siege:'Cerco'};
  const rowKeys = ['melee','ranged','siege'];
  const firstRow = rowKeys.find(row => (enemy.board || []).some(unit => unit.row === row)) || 'melee';
  const modal = document.createElement('div');
  modal.id = 'gwent-relic-modal'; modal.className = 'gwent-target-modal';
  modal.setAttribute('role','dialog'); modal.setAttribute('aria-modal','true');
  const relicNames = {
    reliquia_grande_runa_godrick:'Grande Runa de Godrick', reliquia_runa_nao_nascidos:'Grande Runa dos Não Nascidos',
    reliquia_runa_morte:'Runa da Morte', reliquia_noite_chama:'Espada da Noite e da Chama',
    reliquia_lamina_negra:'Lâmina Negra', reliquia_algemas_margit:'Algemas de Margit'
  };
  modal.innerHTML = `<div class="gwent-target-box"><small class="eyebrow">AÇÃO ÚNICA DA PARTIDA</small><h3>${escapeHTML(relicNames[relicId] || 'Relíquia')}</h3>
    ${needsRow ? `<label class="gwent-relic-choice"><span>FILEIRA INIMIGA</span><select id="gwent-relic-row">${rowKeys.map(row => `<option value="${row}" ${row === firstRow ? 'selected' : ''}>${rowLabels[row]}</option>`).join('')}</select></label>` : ''}
    ${relicId === 'reliquia_noite_chama' ? `<label class="gwent-relic-choice"><span>POSTURA</span><select id="gwent-relic-mode"><option value="noite">Noite — aplicar Geada à fileira</option><option value="chama">Chama — atingir a unidade mais forte</option></select></label>` : ''}
    ${needsTarget ? `<label class="gwent-relic-choice"><span>ALVO</span><select id="gwent-relic-target"></select></label>` : ''}
    <p class="muted">A ativação consome seu turno. A Relíquia só pode ser consumida uma vez por partida.</p>
    <div class="gwent-target-actions"><button type="button" data-gwent-relic-confirm>CONFIRMAR</button><button type="button" class="secondary" data-gwent-relic-cancel>CANCELAR</button></div></div>`;
  const updateTargets = () => {
    if (!needsTarget) return;
    const row = modal.querySelector('#gwent-relic-row')?.value || firstRow;
    const targetSelect = modal.querySelector('#gwent-relic-target');
    const targets = (enemy.board || []).filter(unit => unit.row === row);
    targetSelect.innerHTML = targets.map(unit => `<option value="${escapeHTML(unit.id)}">${escapeHTML(unit.nome)} · ${number(Math.max(1, Number(unit.poder || 0) + Number(unit.bonus || 0)))} poder${Number(unit.escudo || 0) > 0 ? ' · Escudo' : ''}</option>`).join('');
    modal.querySelector('[data-gwent-relic-confirm]').disabled = !targets.length;
  };
  modal.addEventListener('change', event => { if (event.target.id === 'gwent-relic-row') updateTargets(); });
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('[data-gwent-relic-cancel]')) return closeGwentRelicPicker();
    if (!event.target.closest('[data-gwent-relic-confirm]')) return;
    const row = modal.querySelector('#gwent-relic-row')?.value || '';
    const target = needsTarget ? (modal.querySelector('#gwent-relic-target')?.value || '')
      : relicId === 'reliquia_noite_chama' ? (modal.querySelector('#gwent-relic-mode')?.value || 'noite') : '';
    closeGwentRelicPicker();
    sendGwentAction('relic', '', row, [], target);
  });
  document.body.appendChild(modal);
  updateTargets();
  modal.querySelector('select')?.focus();
}

function replaceGwentArenaMarkup(arena, markup) {
  // Reusa os próprios elementos <img> que já carregaram. Substituir o HTML
  // completo sem isso faz o navegador piscar/reabrir todas as artes a cada jogada.
  const reusableImages = new Map();
  arena.querySelectorAll('img[data-card-src]').forEach(image => {
    const key = image.dataset.cardSrc || '';
    if (!key) return;
    if (!reusableImages.has(key)) reusableImages.set(key, []);
    reusableImages.get(key).push(image);
  });

  // Mantém escolhas locais caso o adversário faça uma jogada enquanto o usuário
  // está marcando cartas da troca inicial ou selecionando uma fileira.
  const checkedSwapIds = new Set([...arena.querySelectorAll('[data-gwent-swap]:checked')].map(el => el.value));
  const selectedRows = new Map([...arena.querySelectorAll('select[data-gwent-row]')].map(el => [el.dataset.gwentRow, el.value]));
  const selectedActionRow = arena.querySelector('#gwent-selected-row')?.value || '';
  const focused = document.activeElement && arena.contains(document.activeElement) ? document.activeElement : null;
  let focusInfo = null;
  if (focused) {
    if (focused.id) focusInfo = {id: focused.id};
    else {
      const attr = ['data-gwent-swap', 'data-gwent-row', 'data-gwent-play', 'data-gwent-select-card', 'data-gwent-pass', 'data-gwent-leader-card', 'data-gwent-keep', 'data-gwent-mulligan', 'data-gwent-surrender', 'data-gwent-relic', 'data-gwent-hand-toggle'].find(name => focused.hasAttribute(name));
      if (attr) focusInfo = {attr, value: attr === 'data-gwent-swap' ? focused.value : focused.getAttribute(attr)};
    }
  }

  const template = document.createElement('template');
  template.innerHTML = markup;
  template.content.querySelectorAll('img[data-card-src]').forEach(nextImage => {
    const key = nextImage.dataset.cardSrc || '';
    const list = reusableImages.get(key);
    const previousImage = list && list.length ? list.shift() : null;
    if (previousImage) {
      previousImage.alt = nextImage.alt;
      nextImage.replaceWith(previousImage);
    }
  });
  template.content.querySelectorAll('[data-gwent-swap]').forEach(el => {
    if (checkedSwapIds.has(el.value) && !el.disabled) el.checked = true;
  });
  template.content.querySelectorAll('select[data-gwent-row]').forEach(el => {
    const prior = selectedRows.get(el.dataset.gwentRow);
    if (prior && [...el.options].some(option => option.value === prior)) el.value = prior;
  });
  const nextActionRow = template.content.querySelector('#gwent-selected-row');
  if (nextActionRow && selectedActionRow && [...nextActionRow.options].some(option => option.value === selectedActionRow)) nextActionRow.value = selectedActionRow;

  const scrollX = window.scrollX;
  const scrollY = window.scrollY;
  closeGwentHistoryPopover();
  arena.replaceChildren(template.content);

  if (focusInfo) {
    let target = focusInfo.id ? arena.querySelector(`#${CSS.escape(focusInfo.id)}`) : null;
    if (!target && focusInfo.attr) {
      target = [...arena.querySelectorAll(`[${focusInfo.attr}]`)].find(el =>
        (focusInfo.attr === 'data-gwent-swap' ? el.value : el.getAttribute(focusInfo.attr)) === focusInfo.value
      ) || null;
    }
    try { target?.focus({preventScroll:true}); } catch { /* foco é apenas preservado quando suportado */ }
  }

  // Se o navegador ainda ajustar a âncora da página durante a troca do DOM,
  // restaura a posição sem animação. Não força scroll quando nada se moveu.
  if (Math.abs(window.scrollY - scrollY) > 1 || Math.abs(window.scrollX - scrollX) > 1) {
    const root = document.documentElement;
    const oldBehavior = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    window.scrollTo(scrollX, scrollY);
    root.style.scrollBehavior = oldBehavior;
  }
}


function closeGwentHistoryPopover() {
  if (typeof gwentHistoryPopoverCleanup === 'function') {
    const cleanup = gwentHistoryPopoverCleanup;
    gwentHistoryPopoverCleanup = null;
    cleanup();
  }
}

function bindGwentHistoryPopover(arena) {
  const details = arena?.querySelector('.gwent-history');
  if (!details) return;
  const summary = details.querySelector('summary');
  const sourceList = details.querySelector('ol');
  if (!summary || !sourceList) return;

  details.addEventListener('toggle', () => {
    if (!details.open) {
      closeGwentHistoryPopover();
      return;
    }

    closeGwentHistoryPopover();
    const popover = document.createElement('div');
    popover.className = 'gwent-history-popover';
    popover.setAttribute('role', 'region');
    popover.setAttribute('aria-label', 'Histórico da partida');
    popover.innerHTML = `<ol>${sourceList.innerHTML}</ol>`;
    document.body.appendChild(popover);

    const place = () => {
      if (!popover.isConnected || !summary.isConnected) return;
      const anchor = summary.getBoundingClientRect();
      const width = Math.min(420, Math.max(220, window.innerWidth - 24));
      popover.style.width = `${width}px`;
      const left = Math.max(12, Math.min(window.innerWidth - width - 12, anchor.right - width));
      const maxHeight = Math.min(Math.round(window.innerHeight * 0.55), 420);
      popover.style.maxHeight = `${Math.max(150, maxHeight)}px`;
      const estimatedHeight = Math.min(popover.scrollHeight || maxHeight, maxHeight);
      const below = anchor.bottom + 8;
      const top = below + estimatedHeight <= window.innerHeight - 12
        ? below
        : Math.max(12, anchor.top - estimatedHeight - 8);
      popover.style.left = `${left}px`;
      popover.style.top = `${top}px`;
    };

    const closeFromOutside = event => {
      if (details.contains(event.target) || popover.contains(event.target)) return;
      details.open = false;
      closeGwentHistoryPopover();
    };
    const closeOnEscape = event => {
      if (event.key !== 'Escape') return;
      details.open = false;
      closeGwentHistoryPopover();
      summary.focus({preventScroll: true});
    };
    const reposition = () => place();

    document.addEventListener('pointerdown', closeFromOutside, true);
    document.addEventListener('keydown', closeOnEscape, true);
    window.addEventListener('resize', reposition, {passive: true});
    window.addEventListener('scroll', reposition, true);
    requestAnimationFrame(place);

    gwentHistoryPopoverCleanup = () => {
      document.removeEventListener('pointerdown', closeFromOutside, true);
      document.removeEventListener('keydown', closeOnEscape, true);
      window.removeEventListener('resize', reposition);
      window.removeEventListener('scroll', reposition, true);
      popover.remove();
    };
  });
}

function gwentWeatherSnapshot(data) {
  const raw = data?.weather;
  const map = raw && typeof raw === 'object' && !Array.isArray(raw) ? raw : {};
  const rows = new Set(Array.isArray(data?.weather_rows) ? data.weather_rows.map(String) : []);
  const levels = {};
  for (const row of ['melee', 'ranged', 'siege']) {
    const parsed = Number(map[row] ?? (rows.has(row) ? 1 : 0));
    levels[row] = Number.isFinite(parsed) ? Math.max(0, parsed) : 0;
  }
  return levels;
}

function dockGwentLeaderCard(arena) {
  const card = arena?.querySelector('[data-gwent-leader-card]');
  const existing = document.getElementById('gwent-leader-card-dock');
  if (!card) {
    existing?.remove();
    return;
  }
  const dock = existing || document.createElement('div');
  dock.id = 'gwent-leader-card-dock';
  dock.className = 'gwent-leader-card-dock';
  dock.setAttribute('aria-label', 'Carta de líder fixa');
  dock.replaceChildren(card);
  if (!dock.isConnected) document.body.appendChild(dock);
}

function renderGwentArena(data) {
  if (gwentLastRenderedMatch !== null && gwentLastRenderedMatch !== String(data.match_id)) {
    gwentPreviousPowerSnapshot = new Map();
    gwentLastRenderedRound = null;
    gwentLastTurnAnnouncement = null;
    gwentHandOpen = null;
    gwentHandLastPhase = null;
    closeGwentLeaderModal();
  }
  currentGwentData = data;
  const arena = $('#gwent-arena');
  // O modo de duelo é aplicado no ponto de renderização também: protege contra
  // fluxos que abrem uma partida sem passar pelo botão padrão de entrada.
  document.body.classList.add('gwent-match-active');
  document.documentElement.classList.add('gwent-match-active');
  applyGwentArenaTheme();
  arena.hidden = false;
  gwentAlvos = data.alvos || {};
  if (!data.is_your_turn) closeGwentTargetPicker();

  const score = data.score || {};
  const ids = Object.keys(score);
  const my = String(data.your_id || '');
  const enemy = ids.find(id => String(id) !== my);
  const mine = score[my] || {board:[], score:0, crowns:0, hand:0, passed:false};
  const theirs = score[enemy] || {board:[], score:0, crowns:0, hand:0, passed:false};
  gwentBoardCardsById = new Map([...(mine.board || []), ...(theirs.board || [])].map(card => [String(card.id), card]));
  const opponentName = data.opponent?.name || `Jogador ${String(enemy || '').slice(-4)}`;
  const winnerLabel = data.winner_id
    ? (String(data.winner_id) === my ? 'Você venceu' : `${opponentName} venceu`)
    : 'Empate';
  const prep = data.phase === 'mulligan';
  const hand = Array.isArray(data.hand) ? data.hand : [];
  gwentHandCardsById = new Map(hand.map(card => [String(card.id), card]));
  if (gwentSelectedHandCard && !gwentHandCardsById.has(String(gwentSelectedHandCard))) gwentSelectedHandCard = '';
  const myTurnNow = data.status === 'active' && !prep && !!data.is_your_turn && !mine.passed;
  const enemyTurnNow = data.status === 'active' && !prep && !data.is_your_turn && !theirs.passed;
  const handPhase = prep ? 'prep' : data.status === 'finished' ? 'finished' : myTurnNow ? 'mine' : 'enemy';
  if (handPhase !== gwentHandLastPhase) {
    gwentHandOpen = null;
    gwentHandLastPhase = handPhase;
    gwentSelectedHandCard = '';
  }
  // A mão nunca pode ser reaberta manualmente durante o turno adversário.
  // Ao voltar a vez do jogador, o estado nulo revela a mão automaticamente.
  const handIsOpen = prep || (myTurnNow && gwentHandOpen !== false && hand.length > 0);
  arena.classList.toggle('hand-open', handIsOpen);
  arena.classList.toggle('gwent-player-turn', myTurnNow);
  arena.classList.toggle('gwent-opponent-turn', enemyTurnNow);

  const weatherLevels = gwentWeatherSnapshot(data);
  const activeWeatherRows = Object.entries(weatherLevels).filter(([, level]) => level > 0);
  const cardsAlreadyOnBoard = new Set(
    [...arena.querySelectorAll('.gwent-board-card[data-card-id]')].map(card => String(card.dataset.cardId))
  );
  const previousPowerSnapshot = gwentPreviousPowerSnapshot;
  const nextPowerSnapshot = new Map();
  // Os dois lados usam a mesma ordem vertical para que cada fileira fique frente a frente:
  // Corpo a corpo vs Corpo a corpo, Longa distância vs Longa distância e Cerco vs Cerco.
  const board = (side) => gwentRows.map(([key,label]) => {
    const cards = (side.board || []).filter(card => card.row === key);
    const rowPower = cards.reduce((total, card) => total + Math.max(
      1,
      gwentEffectivePower(card, weatherLevels[key] || 0)
    ), 0);
    const hasEnteringCard = cards.some(card => !cardsAlreadyOnBoard.has(String(card.id)));
    const weatherValue = weatherLevels[key] || 0;
    const effectTotals = [
      ['sangramento','SANGRAMENTO','🩸'],['geada','GEADA','❄'],
      ['podrida','PODRIDÃO','☣'],['loucura','LOUCURA','🔥']
    ].map(([field,label,glyph]) => ({field,label,glyph,count:cards.reduce((sum, card) => sum + Number(card[field] || 0), 0)})).filter(item => item.count > 0);
    const rowEffectsMarkup = `${weatherValue > 0 ? '<i class="gwent-row-effect-chip is-weather" title="Chuva ativa">☂ CHUVA</i>' : ''}${effectTotals.map(item => `<i class="gwent-row-effect-chip effect-${item.field}" title="${item.label}: ${item.count} marca(s)">${item.glyph} ${number(item.count)}</i>`).join('')}`;
    const weatherDrops = weatherValue > 0 ? Array.from({length: 52}, (_, i) => {
      // Valores determinísticos: a textura não muda aleatoriamente entre renderizações.
      const seed = (i * 37 + key.length * 19 + (key.charCodeAt(0) || 0)) % 101;
      const left = (seed * 97) % 100;
      const duration = 0.46 + ((i * 13) % 8) * 0.075;
      const delay = -(((i * 17) % 100) / 100 * duration);
      const length = 16 + ((i * 7) % 12);
      const alpha = (0.62 + ((i * 11) % 4) * 0.09).toFixed(2);
      return `<i class="gwent-weather-drop" style="--drop-left:${left}%;--drop-duration:${duration.toFixed(2)}s;--drop-delay:${delay.toFixed(2)}s;--drop-length:${length}px;--drop-alpha:${alpha}"></i>`;
    }).join('') : '';
    const weatherMarkup = weatherValue > 0
      ? `<div class="gwent-weather-vfx" aria-hidden="true" data-weather-vfx="v5" data-weather-level="${Math.min(3, weatherValue)}" style="--weather-intensity:${Math.min(3, weatherValue)}">
          <span class="gwent-weather-cloud gwent-weather-cloud-back"></span>
          <span class="gwent-weather-cloud gwent-weather-cloud-front"></span>
          <span class="gwent-weather-rain"></span>
          <span class="gwent-weather-drop-layer">${weatherDrops}</span>
          <span class="gwent-weather-mist"></span>
          <span class="gwent-weather-lightning"></span>
        </div>`
      : '';
    const cardsMarkup = cards.map(card => {
      const cardId = String(card.id);
      const previousPower = previousPowerSnapshot.has(cardId) ? previousPowerSnapshot.get(cardId) : null;
      const currentPower = gwentEffectivePower(card, weatherValue);
      nextPowerSnapshot.set(cardId, currentPower);
      return gwentCardView(card, !cardsAlreadyOnBoard.has(cardId), weatherValue, previousPower);
    }).join('');
    return `<div class="gwent-row ${hasEnteringCard ? 'has-entering' : ''} ${weatherValue > 0 ? 'has-weather' : ''}" data-row="${escapeHTML(key)}" data-weather-active="${weatherValue > 0 ? 'true' : 'false'}" data-weather-level="${weatherValue}" data-card-count="${cards.length}" style="--row-card-count:${Math.max(1, cards.length)};--row-card-height:${Math.max(112, 238 - Math.max(0, cards.length - 1) * 18)}px">
      ${weatherMarkup}
      <h4><span class="gwent-row-name">${escapeHTML(label)}</span><small class="gwent-row-effects">${rowEffectsMarkup}</small><b class="gwent-row-power">${number(rowPower)}</b></h4>
      <div class="gwent-board-cards">${cardsMarkup}</div>
    </div>`;
  }).join('');

  const eventHistory = Array.isArray(data.event_log) ? data.event_log : [];
  const activeWeatherLabel = activeWeatherRows.map(([row]) => ({melee:'Corpo a corpo',ranged:'Longa distância',siege:'Cerco'}[row] || row)).join(' · ');
  const eventPanel = `<details class="gwent-history"><summary>Histórico · ${number(eventHistory.length)}</summary><ol>${eventHistory.slice().reverse().map(item => `<li>${escapeHTML(item)}</li>`).join('') || '<li>A partida ainda não possui jogadas registradas.</li>'}</ol></details>`;
  const reward = data.reward;
  const rewardPanel = data.status === 'finished' && reward
    ? `<aside class="gwent-reward-panel"><b>Recompensas</b><span>+${number(reward.reward_xp)} XP · +${number(reward.reward_denarios)} Denários · ${number(reward.mmr_delta)} MMR</span></aside>`
    : '';
  const phaseLabel = data.status === 'finished'
    ? winnerLabel
    : prep
      ? (data.mulligan_done ? 'AGUARDANDO' : 'PREPARAÇÃO')
      : 'EM ANDAMENTO';
  const prepPanel = prep
    ? `<div class="gwent-prep"><span>Troque até 2 cartas ou mantenha sua mão · ${number(data.draw_count || 0)} reserva(s)</span><button class="secondary" data-gwent-keep ${data.mulligan_done ? 'disabled' : ''}>Manter mão</button><button class="primary" data-gwent-mulligan ${data.mulligan_done ? 'disabled' : ''}>Trocar selecionadas</button></div>`
    : '';
  const canPlayFromHand = data.status === 'active' && !!data.is_your_turn && !prep && !mine.passed;
  const handCardCount = Math.max(1, hand.length);
  const handCardWidth = hand.length
    ? Math.max(112, Math.min(208, Math.floor((window.innerWidth - 64 - Math.max(0, hand.length - 1) * 10) / hand.length)))
    : 210;
  const handMaxWidth = Math.min(Math.max(320, window.innerWidth - 48), hand.length * handCardWidth + Math.max(0, hand.length - 1) * 10);
  const handLayoutStyle = `--hand-count:${handCardCount};--hand-max-width:${handMaxWidth}px`;
  const handMarkup = hand.map(card => {
    const cardId = escapeHTML(card.id);
    const cardName = escapeHTML(card.nome || 'Carta');
    const swapControl = prep
      ? `<input class="gwent-hand-swap-input" type="checkbox" data-gwent-swap value="${cardId}" aria-label="Marcar ${cardName} para troca" ${data.mulligan_done || !(data.draw_count > 0) ? 'disabled' : ''}>`
      : '';
    return `<article class="gwent-unit gwent-hand-card" data-gwent-hand-card="${cardId}" role="button" tabindex="0" aria-pressed="false" aria-label="Selecionar ${cardName}" title="${cardName}">
      ${cardImageMarkup(card, cardName)}
      ${swapControl}
    </article>`;
  }).join('') || '<div class="gwent-empty-hand">Sua mão está vazia.</div>';

  const factionName = data.faction || mine.faction || '—';
  const leaderIdForCard = String(data.leader_id || '');
  const leaderSimpleText = gwentLeaderSimpleExplanation(leaderIdForCard, data.leader_description || 'Habilidade especial do líder.');
  const leaderCardMarkup = `<button type="button" class="gwent-leader-card ${data.leader_used ? 'is-spent' : ''}" data-gwent-leader-card title="Consultar e ativar a habilidade de ${escapeHTML(data.leader_name || 'líder')}" aria-label="Carta do líder ${escapeHTML(data.leader_name || 'líder')}. ${escapeHTML(leaderSimpleText)}">
      <span class="gwent-leader-card-art">${gwentLeaderArtMarkup(leaderIdForCard, 'gwent-leader-full-image')}<i hidden>${gwentLeaderIcon(leaderIdForCard)}</i></span>
      <span class="gwent-leader-card-meta"><small class="gwent-leader-eyebrow">CARTA DE LÍDER</small><b>${escapeHTML(data.leader_name || 'Líder')}</b><small>${escapeHTML(factionName)}</small><span class="gwent-leader-card-ability">${escapeHTML(leaderSimpleText)}</span><em>${data.leader_used ? 'HABILIDADE USADA' : 'CLIQUE PARA VER / ATIVAR'}</em></span>
    </button>`;
  const actionDisabled = !data.is_your_turn || data.status !== 'active' || prep;
  const myTurn = myTurnNow;
  const enemyTurn = enemyTurnNow;
  const turnClass = prep ? 'prep' : data.status === 'finished' ? 'finished' : myTurn ? 'mine' : enemyTurn ? 'enemy' : 'passed';
  const turnHeadline = prep ? (data.mulligan_done ? 'PREPARAÇÃO CONCLUÍDA' : 'PREPARE SUA MÃO')
    : data.status === 'finished' ? 'PARTIDA ENCERRADA'
    : myTurn ? 'SUA VEZ' : (data.is_ai_match ? 'VEZ DA NARA' : 'VEZ DO ADVERSÁRIO');
  const turnSubline = prep ? 'Troque até duas cartas ou mantenha sua mão.'
    : data.status === 'finished' ? 'Confira o resultado da partida.'
    : mine.passed ? 'Aguarde o adversário concluir a rodada.'
    : myTurn ? 'Escolha uma carta para jogar.' : (data.is_ai_match ? 'A NARA está calculando a jogada.' : 'Aguarde a jogada do adversário.');
  const turnAnnouncement = data.status === 'finished' ? 'finished' : prep ? 'prep' : mine.passed ? 'passed' : myTurn ? 'mine' : 'enemy';
  if (data.status === 'active' && turnAnnouncement !== gwentLastTurnAnnouncement) {
    if (myTurn) window.gwentBanner?.('SUA VEZ!');
    else if (!prep && data.is_ai_match) window.gwentBanner?.('VEZ DA NARA');
    else if (!prep) window.gwentBanner?.('VEZ DO ADVERSÁRIO');
  }
  gwentLastTurnAnnouncement = turnAnnouncement;

  const enemyBoardMarkup = board(theirs);
  const myBoardMarkup = board(mine);
  const nextBoardIds = new Set([...(mine.board || []), ...(theirs.board || [])].map(card => String(card.id)));
  const sameRenderedRound = gwentLastRenderedMatch === String(data.match_id) && gwentLastRenderedRound === Number(data.round);
  gwentAnimateRemovedBoardCards(arena, nextBoardIds, sameRenderedRound);
  gwentPreviousPowerSnapshot = nextPowerSnapshot;
  gwentLastRenderedMatch = String(data.match_id);
  gwentLastRenderedRound = Number(data.round);

  replaceGwentArenaMarkup(arena, `<div class="gwent-arena-head">
      <div class="gwent-arena-title"><small class="eyebrow">GWENT DO COLISEU · RODADA ${number(data.round)} / 3</small><h2>Arena <span>${escapeHTML(phaseLabel)}</span></h2><p class="gwent-log">${activeWeatherRows.length ? `⛈ CLIMA ATIVO · ${escapeHTML(activeWeatherLabel)}` : escapeHTML(data.last_event || `${opponentName} · ${data.opponent?.faction || 'Facção não informada'}`)}</p></div>
      <div class="gwent-turn-indicator ${turnClass}" role="status" aria-live="polite"><span class="gwent-turn-dot" aria-hidden="true"></span><strong>${turnHeadline}</strong>${prep || data.status === 'finished' || mine.passed ? `<small>${turnSubline}</small>` : ''}</div>
      <div class="gwent-arena-head-actions">${eventPanel}<button type="button" class="gwent-theme-toggle${gwentEldenRingThemeEnabled() ? ' is-active' : ''}" data-gwent-theme-toggle aria-pressed="${gwentEldenRingThemeEnabled()}">${gwentEldenRingThemeEnabled() ? '✧ ELDEN RING · ATIVO' : '✧ TEMA ELDEN RING'}</button><button type="button" class="gwent-exit" data-gwent-exit>Voltar ao lobby</button></div>
    </div>
    <div class="gwent-arena-toolbar">
      ${rewardPanel}
    </div>
    <div class="gwent-battlefield" aria-label="Campo de batalha">
      <section class="gwent-board-side gwent-board-enemy ${enemyTurn ? 'is-active' : ''} ${theirs.passed ? 'is-passed' : ''}"><h3><span>CAMPO DE ${escapeHTML(opponentName)}${data.is_ai_match ? ' · NARA IA' : ''}</span>${enemyTurn ? '<b>JOGANDO AGORA</b>' : theirs.passed ? '<b>PASSOU</b>' : ''}</h3>${enemyBoardMarkup}</section>
      <div class="gwent-battle-line" aria-hidden="true"><span>LINHA DE CONFRONTO</span></div>
      <section class="gwent-board-side gwent-board-mine ${myTurn ? 'is-active' : ''} ${mine.passed ? 'is-passed' : ''}"><h3><span>SEU CAMPO</span>${myTurn ? '<b>SUA VEZ</b>' : mine.passed ? '<b>PASSOU</b>' : ''}</h3>${myBoardMarkup}</section>
    </div>
    <div class="gwent-actions ${prep ? 'is-prep' : ''}">
      <div class="gwent-score gwent-score-you">
        <article><small>VOCÊ</small><strong>${number(mine.score)}</strong><span>${number(mine.crowns)} coroas · ${number(mine.hand)} na mão${mine.passed ? ' · passou' : ''}</span></article>
      </div>
      <div class="gwent-action-center">
        ${prepPanel}
        <div class="gwent-action-buttons">
          <div class="gwent-action-main">
            <button class="gwent-pass-button" data-gwent-pass ${actionDisabled || mine.passed ? 'disabled' : ''}>PASSAR RODADA</button>
          </div>
          <div class="gwent-action-tools">
            <button class="gwent-leader-button" data-gwent-relic ${actionDisabled || !mine.equipped_relic_id || mine.relic_used ? 'disabled' : ''}>ATIVAR RELÍQUIA</button>
            <button class="gwent-surrender-button" data-gwent-surrender ${data.status !== 'active' ? 'disabled' : ''}>DESISTIR</button>
          </div>
        </div>
      </div>
      <div class="gwent-score gwent-score-opponent">
        <article><small>${escapeHTML(opponentName)}</small><strong>${number(theirs.score)}</strong><span>${number(theirs.crowns)} coroas · ${number(theirs.hand)} na mão${theirs.passed ? ' · passou' : ''}</span></article>
      </div>
    </div>
    <section class="gwent-hand-zone ${handIsOpen ? 'is-open' : ''} ${myTurn ? 'is-my-turn' : enemyTurn ? 'is-enemy-turn' : ''}">
      ${leaderCardMarkup}
      <div class="gwent-hand-head">
        <div class="gwent-hand-info"><h3>SUA MÃO <span>${number(hand.length)} CARTAS</span></h3><small>${myTurn ? 'Sua vez: escolha uma carta para jogar' : prep ? 'Marque até duas cartas para trocar' : data.status === 'finished' ? 'Partida encerrada' : 'Sua mão reaparecerá automaticamente na sua vez'}</small></div>
        ${(prep || myTurn) ? `<button type="button" class="gwent-hand-toggle ${handIsOpen ? 'is-open' : ''}" data-gwent-hand-toggle data-count="${number(hand.length)}" aria-expanded="${handIsOpen ? 'true' : 'false'}" aria-controls="gwent-hand-cards">${handIsOpen ? 'OCULTAR CARTAS' : `MOSTRAR MINHA MÃO · ${number(hand.length)}`}</button>` : `<span class="gwent-hand-turn-tag ${enemyTurn ? 'is-enemy' : ''}">${enemyTurn ? 'MÃO PROTEGIDA' : data.status === 'finished' ? 'FIM DE PARTIDA' : 'AGUARDANDO'}</span>`}
      </div>
      <div class="gwent-hand" id="gwent-hand-cards" data-can-play="${canPlayFromHand ? 'true' : 'false'}" style="${handLayoutStyle}" ${handIsOpen ? '' : 'hidden'}>${handMarkup}</div>
    </section>`);
  dockGwentLeaderCard(arena);
  bindGwentHistoryPopover(arena);
  gwentSelectedHandCard = gwentHandCardsById.has(String(gwentSelectedHandCard)) ? gwentSelectedHandCard : '';
}

function showGwentResultOverlay(data, roundResult = null) {
  document.getElementById('gwent-round-result')?.remove();
  const myId = String(data.your_id || '');
  const opponentName = data.opponent?.name || 'Adversário';
  const final = data.status === 'finished';
  const finalWinner = data.winner_id == null ? null : String(data.winner_id);
  const roundOutcome = roundResult?.result || 'draw';
  // O resultado final é decidido pelo total de coroas, não pelo vencedor da última rodada.
  const outcome = final
    ? (finalWinner == null ? 'draw' : finalWinner === myId ? 'win' : 'loss')
    : roundOutcome;
  const headline = final
    ? (outcome === 'win' ? 'VOCÊ VENCEU A PARTIDA' : outcome === 'loss' ? 'VOCÊ PERDEU A PARTIDA' : 'PARTIDA EMPATADA')
    : (outcome === 'win' ? `VOCÊ VENCEU A RODADA ${number(roundResult?.round)}`
      : outcome === 'loss' ? `VOCÊ PERDEU A RODADA ${number(roundResult?.round)}` : `RODADA ${number(roundResult?.round)} EMPATADA`);
  const subline = roundResult
    ? `Você ${number(roundResult.your_score)} × ${number(roundResult.opponent_score)} ${escapeHTML(opponentName)}`
    : (data.last_event || 'Resultado final registrado.');
  const scoreLine = roundResult
    ? `<div class="gwent-result-score"><span>SUA PONTUAÇÃO</span><strong>${number(roundResult.your_score)}</strong><i>×</i><strong>${number(roundResult.opponent_score)}</strong><span>${escapeHTML(opponentName)}</span></div>`
    : `<div class="gwent-result-crowns"><span>SUAS COROAS <b>${number(data.crowns?.[myId] || 0)}</b></span><span>COROAS DO ADVERSÁRIO <b>${number(data.crowns?.[String(data.opponent?.id || '')] || 0)}</b></span></div>`;
  const reward = final && data.reward
    ? `<div class="gwent-result-rewards">Recompensas: +${number(data.reward.reward_xp)} XP · +${number(data.reward.reward_denarios)} Denários · ${number(data.reward.mmr_delta)} MMR</div>` : '';
  const roundHighlights = roundResult?.highlights || {};
  const renderHighlights = (items, heading) => {
    const safeItems = Array.isArray(items) ? items.slice(0, 3) : [];
    if (!safeItems.length) return '';
    return `<div class="gwent-result-highlight-side"><b>${heading}</b><ol>${safeItems.map(item => `<li><span>${escapeHTML(item.name || 'Unidade')} · ${escapeHTML(gwentRowLabel(item.row || ''))}</span><strong>${number(item.power)} P</strong></li>`).join('')}</ol></div>`;
  };
  const highlightsMarkup = renderHighlights(roundHighlights.you, 'SEU CAMPO') + renderHighlights(roundHighlights.opponent, 'CAMPO ADVERSÁRIO');
  const highlightPanel = highlightsMarkup ? `<section class="gwent-result-highlights"><h3>DESTAQUES DA RODADA</h3><p>Unidades com maior poder efetivo no momento do encerramento.</p><div>${highlightsMarkup}</div></section>` : '';
  const overlay = document.createElement('div');
  overlay.id = 'gwent-round-result';
  overlay.className = `gwent-result-overlay ${outcome}`;
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-modal', 'true');
  overlay.setAttribute('aria-labelledby', 'gwent-result-title');
  overlay.innerHTML = `<section class="gwent-result-card"><small class="eyebrow">${final ? 'RESULTADO FINAL' : 'FIM DA RODADA'}</small><h2 id="gwent-result-title">${headline}</h2><p>${subline}</p>${scoreLine}${highlightPanel}${reward}<div class="gwent-result-actions">${final ? '<button type="button" class="primary" data-gwent-exit>VOLTAR AO LOBBY</button>' : '<button type="button" class="primary" data-gwent-result-close>CONTINUAR</button>'}</div></section>`;
  document.body.appendChild(overlay);
  overlay.querySelector('button')?.focus({preventScroll:true});
}

async function parseGwentApiResponse(response) {
  const raw = await response.text();
  try {
    return raw ? JSON.parse(raw.replace(/^\uFEFF/, '').trim()) : {};
  } catch (error) {
    const preview = raw.replace(/\s+/g, ' ').slice(0, 220);
    throw new Error(`Resposta inválida da API Gwent (HTTP ${response.status}): ${preview || 'corpo vazio'}`);
  }
}

async function refreshGwentMatch() {
  if (!currentGwentMatch || gwentActionInFlight) return true;
  // Um único GET por vez; intervalos não podem empilhar requisições lentas.
  if (gwentRefreshPromise) return gwentRefreshPromise;

  const matchId = Number(currentGwentMatch);
  const epoch = gwentRefreshEpoch;
  gwentRefreshPromise = (async () => {
    try {
      const response = await fetch(`/api/gwent/matches/${matchId}`, {credentials:'same-origin', cache:'no-store'});
      const data = await parseGwentApiResponse(response);

      // Descarta respostas antigas se a partida mudou ou houve uma jogada durante o GET.
      if (Number(currentGwentMatch) !== matchId || epoch !== gwentRefreshEpoch) return true;
      if (!response.ok) throw new Error(data.error || 'Não foi possível abrir a partida.');
      if (data.status === 'pending') {
        showNotice('Este convite ainda aguarda resposta. Consulte a lista de desafios para aceitar ou cancelar.', 'info');
        await loadGwentMatches();
        return false;
      }
      if (data.status === 'declined' || data.status === 'cancelled') {
        showNotice(data.status === 'declined' ? 'Este convite foi recusado.' : 'Este convite foi cancelado.', 'info');
        await loadGwentMatches();
        return false;
      }

      // O endpoint é consultado periodicamente, mas a arena só é redesenhada
      // quando o estado realmente muda. Isso mantém as imagens e a mão estáveis.
      const signature = JSON.stringify(data);
      if (signature !== gwentLastRenderSignature) {
        renderGwentArena(data);
        gwentLastRenderSignature = signature;
      }

      const completedRounds = Array.isArray(data.rounds) ? data.rounds : [];
      if (!gwentInitialSnapshotLoaded) {
        // Ao abrir uma partida em andamento, não reproduz resultados antigos.
        // Ao abrir uma partida finalizada pelo histórico, mostra o placar final.
        gwentInitialSnapshotLoaded = true;
        gwentSeenRoundCount = completedRounds.length;
        if (data.status === 'finished') showGwentResultOverlay(data, completedRounds.at(-1) || null);
      } else {
        const newRounds = completedRounds.slice(gwentSeenRoundCount);
        if (newRounds.length) {
          gwentSeenRoundCount = completedRounds.length;
          showGwentResultOverlay(data, newRounds[newRounds.length - 1]);
        } else if (data.status === 'finished' && !gwentPreviouslyFinished) {
          // Rendição ou encerramento administrativo não acrescenta uma rodada.
          showGwentResultOverlay(data, null);
        }
      }
      gwentPreviouslyFinished = data.status === 'finished';
      gwentMatchFinished = data.status === 'finished';
      if (gwentMatchFinished && gwentPoll) { clearInterval(gwentPoll); gwentPoll = null; }
      return true;
    } catch (error) {
      if (Number(currentGwentMatch) === matchId && epoch === gwentRefreshEpoch) {
        showNotice(error.message, 'error');
      }
      return false;
    } finally {
      gwentRefreshPromise = null;
    }
  })();
  return gwentRefreshPromise;
}

async function openGwentMatch(id) {
  document.body.classList.add('gwent-match-active');
  document.documentElement.classList.add('gwent-match-active');
  // Invalida qualquer resposta da partida anterior antes de trocar o contexto.
  gwentRefreshEpoch += 1;
  if (gwentPoll) { clearInterval(gwentPoll); gwentPoll = null; }
  if (gwentRefreshPromise) await gwentRefreshPromise;
  currentGwentMatch = Number(id);
  gwentHandOpen = null;
  gwentHandLastPhase = null;
  gwentSelectedHandCard = '';
  gwentHandCardsById = new Map();
  gwentLastTurnAnnouncement = null;
  gwentMatchFinished = false;
  gwentLastRenderSignature = '';
  gwentInitialSnapshotLoaded = false;
  gwentSeenRoundCount = 0;
  gwentPreviouslyFinished = false;
  document.getElementById('gwent-round-result')?.remove();
  const canOpen = await refreshGwentMatch();
  if (!canOpen) { currentGwentMatch = null; document.getElementById('gwent-leader-card-dock')?.remove(); document.body.classList.remove('gwent-match-active'); document.documentElement.classList.remove('gwent-match-active'); return; }
  if (!gwentMatchFinished) {
    gwentPoll = setInterval(() => {
      if (!document.hidden) refreshGwentMatch();
    }, 3500);
  }
  const arena = $('#gwent-arena');
  const bounds = arena.getBoundingClientRect();
  if (!document.body.classList.contains('gwent-match-active') && (bounds.top < 0 || bounds.bottom > window.innerHeight)) {
    const root = document.documentElement;
    const oldBehavior = root.style.scrollBehavior;
    root.style.scrollBehavior = 'auto';
    arena.scrollIntoView({behavior:'auto', block:'nearest'});
    root.style.scrollBehavior = oldBehavior;
  }
}
async function respondGwentMatch(matchId, action) {
  try {
    const response = await fetch(`/api/gwent/matches/${Number(matchId)}/respond`, {
      method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({action})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível responder ao convite.');
    await loadGwentMatches();
    if (action === 'accept') {
      showNotice('Convite aceito. A partida começou.', 'success');
      await openGwentMatch(data.match_id);
    } else {
      showNotice(action === 'decline' ? 'Convite recusado.' : 'Convite cancelado.', 'success');
    }
  } catch (error) { showNotice(error.message, 'error'); }
}
async function sendGwentAction(action, card_id = '', row = '', card_ids = [], target_id = '') {
  if (!currentGwentMatch || gwentActionInFlight) return;
  const matchId = Number(currentGwentMatch);
  gwentActionInFlight = true;
  // Invalida qualquer GET iniciado antes da jogada para ele não sobrescrever o estado novo.
  gwentRefreshEpoch += 1;
  try {
    const r = await fetch(`/api/gwent/matches/${matchId}/action`, {method:'POST', credentials:'same-origin', headers:{'Content-Type':'application/json'}, body:JSON.stringify({action, card_id, row, card_ids, target_id})});
    const data = await parseGwentApiResponse(r); if (!r.ok) throw new Error(data.error || 'Jogada recusada.');
    if (action === 'weather') {
      const label = ({melee:'Corpo a corpo',ranged:'Longa distância',siege:'Cerco'})[row] || 'fileira selecionada';
      showNotice(`Clima ativado em ${label}.`, 'success');
    }
    if (gwentRefreshPromise) await gwentRefreshPromise;
    if (Number(currentGwentMatch) === matchId) {
      gwentActionInFlight = false;
      await refreshGwentMatch();
    }
  } catch(e) {
    showNotice(e.message, 'error');
  } finally {
    gwentActionInFlight = false;
  }
}

$('#atelier-card').addEventListener('change', () => {
  atelierPromptText = ''; atelierNegativeText = ''; atelierAnalysisText = ''; atelierReferenceUrl = ''; $('#atelier-analysis').value = ''; $('#atelier-prompt').value = ''; $('#atelier-negative').value = ''; $('#atelier-copy-prompt').disabled = true; $('#atelier-copy-prompts').disabled = true; $('#atelier-copy-reference').disabled = true;
  loadAtelierOfficialArt();
});
$('#atelier-generate-prompt').addEventListener('click', generateAtelierPrompt);
$('#atelier-copy-prompt').addEventListener('click', async () => {
  const button = $('#atelier-copy-prompt');
  const selected = selectedAtelierTarget();
  if (!selected || !atelierPromptText || !atelierAnalysisText || !atelierReferenceUrl) {
    showNotice('Gere primeiro a análise artística, o prompt fixo e a referência da facção.', 'error');
    return;
  }
  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'GERANDO PDF...';
  try {
    const response = await fetch('/api/gwent/atelier/pdf', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ card_id: selected.cardId, exemplar_id: selected.exemplarId })
    });
    if (!response.ok) {
      let message = 'Não foi possível gerar o PDF.';
      try { const data = await response.json(); message = data.error || message; } catch {}
      throw new Error(message);
    }
    const pdfBlob = await response.blob();
    if (pdfBlob.type !== 'application/pdf' || !pdfBlob.size) {
      throw new Error('O servidor não retornou um PDF válido.');
    }
    const objectUrl = URL.createObjectURL(pdfBlob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = `narabot-${String($('#atelier-card option:checked')?.textContent || 'carta').trim().replace(/[^\p{L}\p{N}-]+/gu, '-')}-criacao.pdf`;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(objectUrl), 60000);
    showNotice('PDF baixado: Prompt fixo, Análise artística e referência visual na última página.', 'success');
  } catch (error) {
    showNotice(error.message || 'Falha ao gerar o PDF para IA.', 'error');
  } finally {
    button.textContent = originalLabel;
    button.disabled = !(atelierAnalysisText && atelierPromptText && atelierReferenceUrl);
  }
});

$('#atelier-copy-prompts').addEventListener('click', async () => {
  const button = $('#atelier-copy-prompts');
  const analysis = String($('#atelier-analysis')?.value || atelierAnalysisText || '').trim();
  const fixedPrompt = String($('#atelier-prompt')?.value || atelierPromptText || '').trim();

  if (!analysis || !fixedPrompt) {
    showNotice('Gere primeiro a Análise artística e o Prompt fixo.', 'error');
    button.disabled = true;
    return;
  }

  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'COPIANDO OS 2 PROMPTS...';
  try {
    const text =
      `PROMPT FIXO\n${fixedPrompt}\n\n` +
      `ANÁLISE ARTÍSTICA (PT)\n${analysis}`;
    await atelierCopyPlainText(text);
    showNotice('Os dois prompts foram copiados. Nenhuma imagem foi incluída nesta cópia.', 'success');
  } catch (error) {
    showNotice(error.message || 'Não foi possível copiar os prompts.', 'error');
  } finally {
    button.textContent = originalLabel;
    button.disabled = !(analysis && fixedPrompt);
  }
});

$('#atelier-copy-reference').addEventListener('click', async () => {
  const button = $('#atelier-copy-reference');
  const referenceUrl = String(
    atelierReferenceUrl || $('#atelier-reference-preview')?.getAttribute('src') || ''
  ).trim();

  if (!referenceUrl) {
    showNotice('Gere primeiro a referência visual da facção.', 'error');
    button.disabled = true;
    return;
  }

  const originalLabel = button.textContent;
  button.disabled = true;
  button.textContent = 'COPIANDO IMAGEM...';
  try {
    const response = await fetch(referenceUrl, { credentials: 'same-origin', cache: 'no-store' });
    if (!response.ok) {
      throw new Error(`Não foi possível carregar a imagem de referência (HTTP ${response.status}).`);
    }

    const sourceBlob = await response.blob();
    if (!sourceBlob.type.startsWith('image/')) {
      throw new Error('O servidor não retornou uma imagem válida.');
    }

    const pngBlob = await atelierEnsurePng(sourceBlob);

    if (!navigator.clipboard?.write || !window.ClipboardItem) {
      // Fallback explícito: entrega somente a imagem como arquivo, sem afirmar que foi copiada.
      atelierDownloadBlob(pngBlob, `referencia-${referenceUrl.split('/').pop() || 'faccao.png'}`);
      showNotice(
        'Este navegador não permite copiar imagens diretamente. A imagem de referência foi baixada; anexe o PNG manualmente.',
        'warning'
      );
      return;
    }

    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': pngBlob })
    ]);
    showNotice('Somente a imagem de referência foi copiada. Nenhum prompt foi incluído.', 'success');
  } catch (error) {
    showNotice(
      `Não foi possível copiar a imagem de referência: ${error.message || 'erro desconhecido'}.`,
      'error'
    );
  } finally {
    button.textContent = originalLabel;
    button.disabled = !referenceUrl;
  }
});

$('#atelier-image').addEventListener('change', () => {
  const file = $('#atelier-image').files?.[0];
  const preview = $('#atelier-preview');
  if (atelierPreviewUrl) URL.revokeObjectURL(atelierPreviewUrl);
  atelierPreviewUrl = '';
  if (!file) { preview.hidden = true; $('#atelier-submit').disabled = true; return; }
  if (!['image/png','image/jpeg','image/webp'].includes(file.type) || file.size > 8 * 1024 * 1024) {
    showNotice('Formato inválido ou arquivo acima de 8 MB.', 'error'); preview.hidden = true; $('#atelier-submit').disabled = true; return;
  }
  atelierPreviewUrl = URL.createObjectURL(file); preview.src = atelierPreviewUrl; preview.hidden = false; $('#atelier-submit').disabled = false;
});
$('#atelier-submit').addEventListener('click', submitAtelierArt);
document.addEventListener('click', event => {
  const approve = event.target.closest('[data-atelier-approve]');
  const reject = event.target.closest('[data-atelier-reject]');
  if (approve) decideAtelierSubmission(Number(approve.dataset.atelierApprove), true);
  if (reject) decideAtelierSubmission(Number(reject.dataset.atelierReject), false);
});

$('#gwent-faction').addEventListener('change', () => { renderGwentLeaderOptions(); renderGwentBuilder(); });
$('#gwent-leader').addEventListener('change', () => { renderGwentLeaderOptions($('#gwent-leader').value); renderGwentBuilder(); });
$('#gwent-card-search').addEventListener('input', renderGwentBuilder);
$('#gwent-filter-faction').addEventListener('change', renderGwentBuilder);
$('#gwent-filter-rarity').addEventListener('change', renderGwentBuilder);
$('#gwent-save-deck').addEventListener('click', saveGwentDeck);
$('#gwent-reset-deck').addEventListener('click', resetGwentDeck);
$('#atelier-remove-all-art')?.addEventListener('click', removeAllAtelierArts);
$('#atelier-leader-art-select')?.addEventListener('change', updateAtelierLeaderArtPreview);
$('#atelier-leader-art-file')?.addEventListener('change', () => {
  const file = $('#atelier-leader-art-file')?.files?.[0];
  const status = $('#atelier-leader-art-status');
  if (file && status) status.textContent = `${file.name} selecionado · ${Math.max(1, Math.round(file.size / 1024))} KB. A imagem será normalizada para 1200 × 960 px (5:4).`;
});
$('#atelier-leader-art-upload')?.addEventListener('click', uploadAtelierLeaderArt);
$('#atelier-leader-art-remove')?.addEventListener('click', removeAtelierLeaderArt);
$('#gwent-create-match').addEventListener('click', createGwentMatch);
$('#gwent-solo-match')?.addEventListener('click', createGwentSoloMatch);
$('#gwent-pack-options')?.addEventListener('click', event => {
  const button = event.target.closest('[data-buy-pack]');
  if (!button) return;
  buyGwentPack(button.dataset.packFaction || null, button);
});

function closeGwentHandHoverPreview() {
  document.getElementById('gwent-hand-hover-preview')?.remove();
}
function showGwentImageHoverPreview(source, alt = '') {
  if (!source) return closeGwentHandHoverPreview();
  closeGwentHandHoverPreview();
  const preview = document.createElement('div');
  preview.id = 'gwent-hand-hover-preview';
  preview.setAttribute('aria-hidden', 'true');
  const image = document.createElement('img');
  image.alt = alt || '';
  try {
    const highRes = new URL(source, window.location.origin);
    if (isCardImageUrl(highRes.pathname)) {
      highRes.searchParams.delete('thumb');
      highRes.searchParams.set('detail', '1');
    }
    image.src = `${highRes.pathname}${highRes.search}`;
  } catch {
    image.src = source;
  }
  preview.appendChild(image);
  document.body.appendChild(preview);
}
function showGwentHandHoverPreview(cardId) {
  const card = gwentHandCardsById.get(String(cardId || ''));
  if (!card) return closeGwentHandHoverPreview();
  showGwentImageHoverPreview(imageUrl(card), card.nome || 'Carta');
}

function closeGwentBoardCardModal() {
  document.getElementById('gwent-board-card-modal')?.remove();
}

function openGwentBoardCardModal(cardId) {
  const card = gwentBoardCardsById.get(String(cardId || ''));
  if (!card) return;
  closeGwentHandHoverPreview();
  closeGwentBoardCardModal();
  closeGwentPlayCardModal();

  const modal = document.createElement('div');
  modal.id = 'gwent-board-card-modal';
  modal.className = 'gwent-board-card-modal';
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-label', `Inspeção de combate: ${card.nome || 'carta'}`);

  const basePower = Number(card.poder || 0);
  const bonus = Number(card.bonus || 0);
  const currentPower = Math.max(1, basePower + bonus);
  const shield = Number(card.escudo || 0);
  const rarityBudget = rarityPower(card);
  const rowLabel = card.row_label || gwentRowLabel(card.row || '');
  const isSpecial = !!card.especial || card.categoria === 'Especial';
  const modalCard = {...card};
  const src = imageUrl(card);
  if (isCardImageUrl(src)) {
    const hi = new URL(src, window.location.origin);
    hi.searchParams.delete('thumb');
    hi.searchParams.set('detail', '1');
    modalCard.image_url = `${hi.pathname}${hi.search}`;
  }

  modal.innerHTML = `
    <section class="gwent-board-card-dialog">
      <button type="button" class="gwent-board-card-close" data-gwent-board-close aria-label="Fechar">×</button>
      <div class="gwent-board-card-art">${cardImageMarkup(modalCard, card.nome || 'Carta')}</div>
      <div class="gwent-board-card-info">
        <small class="gwent-board-card-eyebrow">GWENT DO COLISEU · INSPEÇÃO DE COMBATE</small>
        <h2>${escapeHTML(card.nome || 'Carta')}</h2>
        <div class="gwent-board-card-tags v51-inspection-tags">
          <span><i>${cardSigil(card.faccao || 'Especial')}</i>${escapeHTML(card.faccao || 'Coliseu')}</span>
          <span><i>${cardSigil(card.raridade || 'Carta')}</i>${escapeHTML(card.raridade || 'Carta')}</span>
          <span><i>${cardSigil(isSpecial ? 'Especial' : rowLabel)}</i>${escapeHTML(isSpecial ? 'Carta especial' : rowLabel)}</span>
          <span>EM CAMPO</span>
        </div>
        <div class="gwent-board-card-stats">
          <article><small>PODER ATUAL</small><strong>${number(currentPower)}</strong></article>
          <article><small>BÔNUS</small><strong>${bonus > 0 ? '+' : ''}${number(bonus)}</strong></article>
          <article><small>ESCUDO</small><strong>${number(shield)}</strong></article>
          <article class="gwent-rarity-potency"><small>POTÊNCIA DA RARIDADE</small><strong>${number(rarityBudget)} / 6</strong></article>
        </div>
        <section class="gwent-board-card-ability">
          <small>HABILIDADE</small>
          <strong>${escapeHTML(card.habilidade_nome || 'Sem habilidade especial')}</strong>
          <p>${escapeHTML(card.habilidade_texto || 'Sem habilidade especial.')}</p>
        </section>
        ${card.descricao ? `<section class="gwent-board-card-ability gwent-board-card-lore"><small>DESCRIÇÃO</small><p>${escapeHTML(card.descricao)}</p></section>` : ''}
        <p class="gwent-board-card-note"><strong>Como ler o poder:</strong> o número impresso na carta é o poder-base (${number(basePower)}). O bônus de combate é ${bonus > 0 ? "+" : ""}${number(bonus)}. Por isso, o poder atual é ${number(currentPower)} (poder-base + bônus, com mínimo de 1). A potência da raridade melhora apenas os efeitos da habilidade; ela não é somada ao poder.</p>
        <button type="button" class="gwent-board-card-dismiss" data-gwent-board-close>FECHAR INSPEÇÃO</button>
      </div>
    </section>`;
  document.body.appendChild(modal);
  observeCardImages(modal);
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('[data-gwent-board-close]')) {
      closeGwentBoardCardModal();
    }
  });
  modal.querySelector('[data-gwent-board-close]')?.focus();
}

function closeGwentPlayCardModal() {
  document.getElementById('gwent-play-card-modal')?.remove();
  closeGwentCardPreview();
}
function openGwentPlayCardModal(cardId) {
  const card = gwentHandCardsById.get(String(cardId || ''));
  if (!card) return;
  closeGwentHandHoverPreview();
  closeGwentPlayCardModal();
  const arena = document.getElementById('gwent-arena');
  const hand = arena?.querySelector('#gwent-hand-cards');
  const canPlay = hand?.dataset.canPlay === 'true';
  const prep = !!arena?.querySelector('.gwent-prep');
  const modal = document.createElement('div');
  modal.id = 'gwent-play-card-modal';
  modal.className = 'gwent-play-card-modal';
  modal.dataset.cardId = String(card.id);
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-label', `Preparar jogada: ${card.nome || 'carta'}`);
  const isSpecial = !!(card.especial || String(card.categoria || '').toLowerCase() === 'especial');
  const row = ['melee','ranged','siege'].includes(card.row || card.fileira) ? (card.row || card.fileira) : 'melee';
  const rowNames = {melee:'Corpo a corpo',ranged:'Longa distância',siege:'Cerco'};
  const rowTargetSkills = new Set(['gwent_clima','gwent_nevoa','gwent_chifre','gwent_execucao','gwent_vinculo','gwent_muralha','gwent_sangramento','gwent_geada_cariana','gwent_podrida','gwent_loucura','gwent_invocacao','gwent_passo']);
  const needsRowChoice = isSpecial && rowTargetSkills.has(String(card.habilidade || ''));
  const options = (isSpecial && needsRowChoice ? [['melee','Corpo a corpo'],['ranged','Longa distância'],['siege','Cerco']] : [[row,rowNames[row]]])
    .map(([v,l]) => `<option value="${v}" ${row === v ? 'selected' : ''}>${l}</option>`).join('');
  const power = isSpecial ? 'Carta especial · efeito tático' : `${number(card.poder)} poder`;
  const stateText = prep ? 'Na preparação, marque a carta para incluí-la na troca.'
    : canPlay && !isSpecial ? `Esta unidade só pode entrar em ${rowNames[row]}.`
    : canPlay && needsRowChoice ? 'Escolha a fileira afetada pelo efeito.'
    : canPlay ? 'Esta tática não exige escolha de fileira.'
    : 'Você poderá jogar esta carta quando chegar sua vez.';
  const modalCard = {...card};
  const modalImageUrl = imageUrl(card);
  if (isCardImageUrl(modalImageUrl)) {
    const highRes = new URL(modalImageUrl, window.location.origin);
    highRes.searchParams.delete('thumb');
    highRes.searchParams.set('detail', '1');
    modalCard.image_url = `${highRes.pathname}${highRes.search}`;
  }
  modal.innerHTML = `
    <section class="gwent-play-card-dialog">
      <button type="button" class="gwent-play-card-close" data-gwent-modal-close aria-label="Fechar">×</button>
      <div class="gwent-play-card-art">${cardImageMarkup(modalCard, card.nome || 'Carta')}</div>
      <div class="gwent-play-card-info">
        <small class="eyebrow">PREPARAR JOGADA</small>
        <h2>${escapeHTML(card.nome || 'Carta')}</h2>
        <div class="gwent-play-card-tags"><span>${escapeHTML(card.raridade || 'Carta')}</span><span>${escapeHTML(power)}</span></div>
        <section class="gwent-play-card-ability">
          <small>HABILIDADE</small>
          <strong>${escapeHTML(card.habilidade_nome || 'Sem habilidade especial')}</strong>
          <p>${escapeHTML(card.habilidade_texto || 'Sem habilidade especial.')}</p>
        </section>
        ${card.descricao ? `<section class="gwent-play-card-ability gwent-play-card-lore"><small>DESCRIÇÃO</small><p>${escapeHTML(card.descricao)}</p></section>` : ''}
        <p class="gwent-play-card-state">${escapeHTML(stateText)}</p>
        <label class="gwent-play-card-row" style="${(!isSpecial || !needsRowChoice) ? 'display:none' : ''}"><span>FILEIRA DO EFEITO</span>
          <select data-gwent-modal-row ${canPlay && !prep && needsRowChoice ? '' : 'disabled'}>${options}</select>
        </label>
        <div class="gwent-play-card-preview" data-gwent-card-preview aria-live="polite">Prévia: confira as unidades que serão afetadas.</div>
        <button type="button" class="gwent-play-card-explain-toggle" data-gwent-explain-toggle aria-expanded="false">EXPLICAÇÃO DETALHADA</button>
        <section class="gwent-play-card-simple-explanation" data-gwent-simple-explanation hidden>
          <small>ENTENDA DE UM JEITO SIMPLES</small><p>${escapeHTML(gwentSimpleExplanation(card))}</p>
          <small>EXEMPLO</small><p>${escapeHTML(gwentSimpleExample(card))}</p>
        </section>
        <button type="button" class="gwent-play-card-confirm" data-gwent-modal-play ${canPlay && !prep ? '' : 'disabled'}>JOGAR CARTA</button>
      </div>
    </section>`;
  document.body.appendChild(modal);
  observeCardImages(modal);
  const previewNode = modal.querySelector('[data-gwent-card-preview]');
  const updatePreview = () => updateGwentCardPreview(card, modal.querySelector('[data-gwent-modal-row]')?.value || row, previewNode);
  updatePreview();
  modal.addEventListener('change', event => { if (event.target.matches('[data-gwent-modal-row]')) updatePreview(); });
  modal.addEventListener('click', event => {
    if (event.target === modal || event.target.closest('[data-gwent-modal-close]')) {
      closeGwentPlayCardModal(); return;
    }
    const explain = event.target.closest('[data-gwent-explain-toggle]');
    if (explain) {
      const panel = modal.querySelector('[data-gwent-simple-explanation]');
      const open = !!panel?.hidden;
      if (panel) panel.hidden = !open;
      explain.setAttribute('aria-expanded', String(open));
      explain.textContent = open ? 'OCULTAR EXPLICAÇÃO' : 'EXPLICAÇÃO DETALHADA';
      return;
    }
    const play = event.target.closest('[data-gwent-modal-play]');
    if (!play || play.disabled) return;
    const selectedRow = modal.querySelector('[data-gwent-modal-row]')?.value || row;
    closeGwentPlayCardModal();
    const targetInfo = gwentOpcoesDoAlvo(String(card.id), selectedRow);
    if (targetInfo && targetInfo.opcoes.length) openGwentTargetPicker(String(card.id), selectedRow, targetInfo);
    else sendGwentAction('play', String(card.id), selectedRow);
  });
  modal.querySelector('[data-gwent-modal-close]')?.focus();
}
// A carta original permanece na mão/campo; o preview HD é uma projeção separada,
// centralizada na viewport, sem retirar a imagem do cartão nem empurrar vizinhas.
document.addEventListener('mouseover', event => {
  const handCard = event.target.closest('[data-gwent-hand-card]');
  if (handCard && !handCard.contains(event.relatedTarget)) {
    showGwentHandHoverPreview(handCard.dataset.gwentHandCard);
    return;
  }
  const boardCard = event.target.closest('.gwent-board-card');
  if (boardCard && !boardCard.contains(event.relatedTarget)) {
    const image = boardCard.querySelector('img[data-card-src]');
    if (image) showGwentImageHoverPreview(image.dataset.cardSrc || image.currentSrc || image.src, image.alt);
  }
});
document.addEventListener('mouseout', event => {
  const handCard = event.target.closest('[data-gwent-hand-card]');
  if (handCard && !handCard.contains(event.relatedTarget)) {
    closeGwentHandHoverPreview();
    return;
  }
  const boardCard = event.target.closest('.gwent-board-card');
  if (boardCard && !boardCard.contains(event.relatedTarget)) closeGwentHandHoverPreview();
});
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') {
    closeGwentPlayCardModal();
    closeGwentBoardCardModal();
    closeGwentLeaderModal();
    closeGwentHandHoverPreview();
    return;
  }
  const handCard = event.target.closest('[data-gwent-hand-card]');
  if (!handCard || (event.key !== 'Enter' && event.key !== ' ')) return;
  event.preventDefault();
  handCard.click();
});

document.addEventListener('click', async event => {
  const themeToggle = event.target.closest('[data-gwent-theme-toggle]');
  if (themeToggle) {
    const enabled = !gwentEldenRingThemeEnabled();
    try {
      if (enabled) window.localStorage.setItem(GWENT_ARENA_THEME_KEY, 'elden-ring');
      else window.localStorage.removeItem(GWENT_ARENA_THEME_KEY);
    } catch (_) {
      // A alternância desta sessão continua funcionando mesmo sem armazenamento local.
    }
    applyGwentArenaTheme(enabled);
    updateGwentArenaThemeButton(themeToggle, enabled);
    return;
  }
  const boardCard = event.target.closest('.gwent-board-card[data-card-id]');
  if (boardCard) {
    openGwentBoardCardModal(boardCard.dataset.cardId);
    return;
  }
  const handCard = event.target.closest('[data-gwent-hand-card]');
  if (handCard) {
    const cardId = String(handCard.dataset.gwentHandCard || '');
    if (document.querySelector('#gwent-arena .gwent-prep')) {
      const swap = handCard.querySelector('[data-gwent-swap]');
      if (swap && !swap.disabled && event.target !== swap) swap.checked = !swap.checked;
      handCard.classList.toggle('is-swap-marked', !!swap?.checked);
    } else {
      gwentSelectedHandCard = cardId;
      openGwentPlayCardModal(cardId);
    }
    return;
  }
  const selectHandCard = event.target.closest('[data-gwent-select-card]');
  if (selectHandCard) {
    updateGwentSelectedCardUI(selectHandCard.dataset.gwentSelectCard);
    return;
  }
  const playSelected = event.target.closest('[data-gwent-play-selected]');
  if (playSelected) {
    const cardId = String(gwentSelectedHandCard || '');
    const rowSelect = $('#gwent-selected-row');
    const row = rowSelect ? rowSelect.value : (gwentHandCardsById.get(cardId)?.row || 'melee');
    if (!cardId || playSelected.disabled) return;
    const info = gwentOpcoesDoAlvo(cardId, row);
    if (info && info.opcoes.length) openGwentTargetPicker(cardId, row, info);
    else sendGwentAction('play', cardId, row);
    return;
  }
  const add = event.target.closest('[data-gwent-add]'); const remove = event.target.closest('[data-gwent-remove]');
  const play = event.target.closest('[data-gwent-play]'); const open = event.target.closest('[data-gwent-open]');
  const respond = event.target.closest('[data-gwent-respond]');
  const closeRoundResult = event.target.closest('[data-gwent-result-close]');
  if (closeRoundResult) {
    document.getElementById('gwent-round-result')?.remove();
    return;
  }
  const handToggle = event.target.closest('[data-gwent-hand-toggle]');
  if (handToggle) {
    if (!document.querySelector('#gwent-arena.gwent-player-turn') && !document.querySelector('#gwent-arena .gwent-prep')) return;
    const zone = handToggle.closest('.gwent-hand-zone');
    const nextOpen = !zone?.classList.contains('is-open');
    gwentHandOpen = nextOpen;
    // O estado da mão também controla a distribuição vertical da arena:
    // recolhida libera altura para o campo; aberta restaura a área da mão.
    document.getElementById('gwent-arena')?.classList.toggle('hand-open', nextOpen);
    zone?.classList.toggle('is-open', nextOpen);
    zone?.querySelector('.gwent-hand')?.toggleAttribute('hidden', !nextOpen);
    handToggle.classList.toggle('is-open', nextOpen);
    handToggle.setAttribute('aria-expanded', String(nextOpen));
    handToggle.textContent = nextOpen ? 'OCULTAR CARTAS' : `MOSTRAR MINHA MÃO · ${handToggle.dataset.count || '0'}`;
    return;
  }
  const exitArena = event.target.closest('[data-gwent-exit]');
  if (exitArena) {
    document.getElementById('gwent-round-result')?.remove();
    document.getElementById('gwent-leader-card-dock')?.remove();
    document.body.classList.remove('gwent-match-active', 'gwent-theme-eldenring');
    document.documentElement.classList.remove('gwent-match-active', 'gwent-theme-eldenring');
    currentGwentMatch = null;
    gwentHandOpen = null;
    gwentHandLastPhase = null;
    gwentSelectedHandCard = '';
    gwentHandCardsById = new Map();
    gwentLastTurnAnnouncement = null;
    gwentPreviousPowerSnapshot = new Map();
    gwentLastRenderedMatch = null;
    gwentLastRenderedRound = null;
    closeGwentLeaderModal();
    gwentRefreshEpoch += 1;
    if (gwentPoll) { clearInterval(gwentPoll); gwentPoll = null; }
    $('#gwent-arena').hidden = true;
    await loadGwentMatches();
    return;
  }
  if (add && gwentDeckIds.length < 12) {
    const card = collection.find(c => c.id === add.dataset.gwentAdd);
    const selected = gwentDeckIds.map(id => collection.find(c => c.id === id)).filter(Boolean);
    if (selected.some(item => (item.card_id || item.id) === (card?.card_id || card?.id))) return showNotice('O deck não pode repetir o mesmo modelo, mesmo usando exemplares diferentes.', 'error');
    const specials = selected.filter(c => c.categoria === 'Especial').length;
    if (card?.categoria === 'Especial' && specials >= 4) return showNotice('O deck aceita no máximo quatro cartas especiais.', 'error');
    gwentDeckIds.push(add.dataset.gwentAdd); renderGwentBuilder();
  }
  if (remove) { gwentDeckIds = gwentDeckIds.filter(id => id !== remove.dataset.gwentRemove); renderGwentBuilder(); }
  if (play) {
    const cardId = play.dataset.gwentPlay;
    const row = document.querySelector(`[data-gwent-row="${CSS.escape(cardId)}"]`)?.value || '';
    const info = gwentOpcoesDoAlvo(cardId, row);
    if (info && info.opcoes.length) openGwentTargetPicker(cardId, row, info); else sendGwentAction('play', cardId, row);
  }
  if (open) openGwentMatch(open.dataset.gwentOpen);
  if (respond) respondGwentMatch(respond.dataset.matchId, respond.dataset.gwentRespond);
  if (event.target.closest('[data-gwent-mulligan]')) {
    const card_ids = [...document.querySelectorAll('[data-gwent-swap]:checked')].map(x => x.value);
    sendGwentAction('mulligan', '', '', card_ids);
  }
  if (event.target.closest('[data-gwent-keep]')) sendGwentAction('keep');
  if (event.target.closest('[data-gwent-pass]')) sendGwentAction('pass');
  if (event.target.closest('[data-gwent-leader-card]')) openGwentLeaderModal();
  if (event.target.closest('[data-gwent-relic]')) openGwentRelicPicker();
  if (event.target.closest('[data-gwent-surrender]')) {
    if (window.confirm('Tem certeza de que deseja desistir? A vitória será concedida ao adversário.')) sendGwentAction('surrender');
  }
});

function showGwentPage() {
  document.querySelectorAll('.page').forEach(el => el.classList.toggle('show', el.id === 'gwent'));
}
async function loadGwentPlayers() {
  if (!currentUser) return;
  try {
    await fetch('/api/presence/heartbeat', {method:'POST', credentials:'same-origin'});
    const response = await fetch('/api/players', {credentials:'same-origin', cache:'no-store'});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Não foi possível carregar jogadores.');
    const players = (data.players || []).filter(player => !player.is_self);
    $('#gwent-opponent').innerHTML = '<option value="">Selecione um adversário</option>' + players.map(player => {
      const status = player.web_online ? ' · online no site' : ` · Discord: ${player.discord_presence}`;
      return `<option value="${escapeHTML(player.id)}">${escapeHTML(player.name)}${escapeHTML(status)}</option>`;
    }).join('');
  } catch (error) {
    const select = $('#gwent-opponent');
    if (select) select.innerHTML = `<option value="">${escapeHTML(error.message || 'Não foi possível carregar jogadores.')}</option>`;
    console.error('Falha ao carregar jogadores do Gwent:', error);
    showNotice(error.message, 'error');
  }
}

loadAccount().then(async () => {
  showGwentPage();
  if (!currentUser) return;
  await Promise.all([loadGwentDeck(), loadGwentMatches(), loadGwentPlayers(), loadDropHistory(), loadAtelier(), loadGwentStore()]);
  window.setInterval(loadGwentPlayers, 30000);
  gwentListPoll = window.setInterval(loadGwentMatches, 12000);
  const requested = new URLSearchParams(window.location.search).get('gwent');
  if (requested && /^\d+$/.test(requested)) openGwentMatch(requested);
});

/* Abertura de pacote: cartas viradas que se revelam uma a uma (clique para pular) */
function revealPack() {
  const box = document.querySelector('#gwent-pack-results .gwent-pack-opened');
  if (!box) return;
  const items = [...box.querySelectorAll('article.pk')];
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  items.forEach(el => el.classList.add('pk-hide'));
  const order = items.map((el, i) => i).sort((x, y) => (RARANK[items[x].dataset.r] || 0) - (RARANK[items[y].dataset.r] || 0));
  let timers = [];
  const show = el => { el.classList.remove('pk-hide'); el.classList.add('pk-show'); };
  order.forEach((idx, n) => timers.push(setTimeout(() => show(items[idx]), 500 + n * 750)));
  box.addEventListener('click', () => { timers.forEach(clearTimeout); items.forEach(show); }, { once: true });
  const h = box.querySelector('h4'); if (h) h.insertAdjacentHTML('afterend', '<small class="pk-skip">Clique para revelar tudo</small>');
}
const RARANK = { comum: 0, rara: 1, epica: 2, lendaria: 3, mitica: 4, primordial: 5, singular: 6 };

// --- Hub: início, comunidade e Nara (dados locais, sem custo de IA). ---
const hubFmt = (iso) => { const d = new Date(String(iso).replace(' ', 'T') + (String(iso).includes('Z') || String(iso).includes('+') ? '' : 'Z')); if (isNaN(d)) return ''; const m = Math.max(0, (Date.now() - d) / 60000); return m < 60 ? `${Math.floor(m) || 1} min` : m < 1440 ? `${Math.floor(m / 60)} h` : `${Math.floor(m / 1440)} d`; };
const hubAvatar = (url, name) => url ? `<img class="hub-av" src="${escapeHTML(url)}" alt="" loading="lazy">` : `<span class="hub-av">${escapeHTML((name || '?')[0].toUpperCase())}</span>`;
const hubName = (r) => `<span class="rank-name"${/^#[0-9a-f]{6}$/i.test(r.cor || '') ? ` style="color:${r.cor}"` : ''}>${r.emblema ? escapeHTML(r.emblema) + ' ' : ''}${escapeHTML(r.name)}</span>`;
const hubRows = (rows, unit) => rows.length ? rows.map(r => `<div class="rank-row${r.pos <= 3 ? ' top' + r.pos : ''}"><b class="rank-pos">${r.pos <= 3 ? ['🥇','🥈','🥉'][r.pos - 1] : r.pos}</b>${hubAvatar(r.avatar, r.name)}${hubName(r)}<strong>${number(r.valor)} <small>${unit}</small></strong></div>`).join('') : '<p class="muted">Ainda sem dados.</p>';
async function loadHub() {
  try {
    const r = await fetch('/api/hub/overview', {credentials: 'same-origin', cache: 'no-store'});
    if (!r.ok) return;
    const d = await r.json(), s = d.server;
    $('#hub-server').textContent = s.name;
    $('#hub-members').textContent = number(s.members); $('#hub-online').textContent = number(s.online); $('#hub-onsite').textContent = number(s.on_site);
    const icon = $('#hub-icon'); if (s.icon) { icon.src = s.icon; icon.hidden = false; }
    const inv = $('#hub-invite'); if (s.invite) { inv.href = s.invite; inv.hidden = false; }
    if (!d.authenticated) return;
    const m = d.me;
    $('#profile-name').dataset.n = m.name || 'Conta Discord'; $('#profile-status').dataset.s = m.patente; $('#profile-name').textContent = m.name || 'Conta Discord'; $('#profile-status').textContent = m.patente;
    if (m.avatar) $('.profile .avatar').innerHTML = `<img src="${escapeHTML(m.avatar)}" alt="" style="width:100%;height:100%;border-radius:50%">`;
    $('#hub-me-name').textContent = m.name || 'Você'; $('#hub-me-rank').textContent = `#${number(m.posicao)} no ranking`;
    if (m.prefs) { visSet(m.prefs, false); window.visServer = m.prefs; }
    const pf = m.prefs || {};
    const pct = Math.min(100, Math.round(m.xp_nivel_atual / Math.max(1, m.xp_nivel_total) * 100));
    $('#hub-me-body').innerHTML = `<div class="me-banner"><span class="me-emb">${escapeHTML(pf.emblema || '⚔')}</span><b>${escapeHTML(m.patente)}</b></div>${pf.frase ? `<p class="me-quote">“${escapeHTML(pf.frase)}”</p>` : ''}<div class="me-level"><b>Nível ${m.nivel}</b><span>${escapeHTML(m.patente)}</span></div><div class="xpbar" title="${pct}%"><i style="width:${pct}%"></i></div><small class="muted">${number(m.xp_nivel_atual)} / ${number(m.xp_nivel_total)} XP para o próximo nível</small><div class="me-stats"><div><b>${number(m.platinas)}</b><small>Platinas</small></div><div><b>${number(m.zerados)}</b><small>Zerados</small></div><div><b>${number(m.runs)}</b><small>Runs</small></div><div><b>${number(m.denarios)}</b><small>Denários</small></div></div>${m.pendentes ? `<p class="muted">⏳ ${m.pendentes} envio(s) aguardando aprovação.</p>` : ''}`;
    $('#hub-tops').innerHTML = [['xp','Mais XP','XP'],['platinas','Platinas','plat.'],['zerados','Zerados','jogos']].map(([k, t, u]) => `<section class="hub-card"><h4>${t}</h4>${hubRows(d.top[k], u)}</section>`).join('');
    $('#hub-recent').innerHTML = d.recent.length ? d.recent.map(a => `<div class="recent-item"><i>${a.tipo === 'platina' ? '💎' : '🏆'}</i><div><b>${escapeHTML(a.user)}</b> ${a.tipo === 'platina' ? 'platinou' : 'zerou'} <b>${escapeHTML(a.game)}</b></div><small>${hubFmt(a.quando)}</small></div>`).join('') : '<p class="muted">Nenhuma conquista recente.</p>';
  } catch (e) { /* hub é complementar: falha silenciosa */ }
}
let hubRank = 'xp';
async function loadRank(tipo = hubRank) {
  hubRank = tipo;
  document.querySelectorAll('#rank-seg button').forEach(b => b.classList.toggle('on', b.dataset.rank === tipo));
  try {
    const r = await fetch(`/api/hub/ranking?tipo=${tipo}&limite=25`, {credentials: 'same-origin', cache: 'no-store'});
    if (!r.ok) return;
    const d = await r.json(), u = d.label.toLowerCase(), t = d.rows.slice(0, 3);
    $('#rank-podium').innerHTML = t.length === 3 ? `<div class="podium">${[1, 0, 2].map(i => `<div class="pod p${i + 1}">${hubAvatar(t[i].avatar, t[i].name)}<b>${hubName(t[i])}</b><small>${number(t[i].valor)} ${u}</small><div class="pod-step">${i + 1}</div></div>`).join('')}</div>` : '';
    $('#rank-list').innerHTML = hubRows(t.length === 3 ? d.rows.slice(3) : d.rows, u);
  } catch (e) {}
}
async function loadCommunityPlayers() {
  try {
    const r = await fetch('/api/players', {credentials: 'same-origin', cache: 'no-store'});
    if (!r.ok) return;
    const d = await r.json(), q = ($('#players-search').value || '').toLowerCase();
    const st = {online: 'Online', idle: 'Ausente', dnd: 'Ocupado', offline: 'Offline'};
    $('#players-list').innerHTML = d.players.filter(p => p.name.toLowerCase().includes(q)).slice(0, 60).map(p => `<div class="player-chip">${hubAvatar(p.avatar, p.name)}<i class="dot ${p.web_online ? 'on' : p.discord_presence}"></i><span>${escapeHTML(p.name)}</span><small>${p.web_online ? 'no site' : st[p.discord_presence] || ''}</small></div>`).join('') || '<p class="muted">Ninguém encontrado.</p>';
  } catch (e) {}
}
function naraSay(txt, who) { const log = $('#nara-log'), p = document.createElement('p'); p.className = `nara-msg ${who}`; p.textContent = txt; log.appendChild(p); log.scrollTop = log.scrollHeight; return p; }
async function naraAsk(q) {
  if (!currentUser) { naraSay('Entre com Discord para falar comigo.', 'bot'); return; }
  naraSay(q, 'me'); const wait = naraSay('…', 'bot');
  try {
    const r = await fetch('/api/hub/nara', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({message: q})});
    const d = await r.json(); wait.textContent = d.reply || d.error || 'Algo deu errado.';
    (d.suggestions || []).forEach(s => { const b = document.createElement('button'); b.type = 'button'; b.className = 'nara-sug'; b.textContent = s; b.onclick = () => naraAsk(s); $('#nara-log').appendChild(b); });
  } catch (e) { wait.textContent = 'Sem conexão com o servidor.'; }
}
$('#nara-form')?.addEventListener('submit', (e) => { e.preventDefault(); const i = $('#nara-input'), q = i.value.trim(); if (q) { i.value = ''; naraAsk(q); } });
$('#rank-seg')?.addEventListener('click', (e) => { const b = e.target.closest('[data-rank]'); if (b) loadRank(b.dataset.rank); });
$('#players-search')?.addEventListener('input', loadCommunityPlayers);
document.addEventListener('click', (e) => { if (e.target.closest('[data-tab="community"],[data-goto="community"]')) { loadRank(); loadCommunityPlayers(); } });
loadHub(); setTimeout(() => { if (currentUser) { loadRank(); loadCommunityPlayers(); } }, 1200);
setInterval(() => { if (!document.hidden && $('#tab-home')?.classList.contains('show')) loadHub(); }, 60000);

// --- Personalização visual: tema + cor + emblema + frase (salvos no perfil). ---
const VIS_TEMAS = [['cinzas', 'Cinzas', '#9b78c4'], ['fogueira', 'Fogueira', '#ff9a3c'], ['abismo', 'Abismo', '#5fd0d6'], ['veneno', 'Veneno', '#9be564'], ['sangue', 'Sangue', '#e0525c'], ['ametista', 'Ametista', '#d9a8ff']];
const VIS_EMB = ['⚔', '🛡', '🔥', '💀', '🐉', '🌙', '👑', '🗡', '🏹', '☠', '🦅', '⚜'];
let vis = {tema: 'cinzas', cor: '', frase: '', emblema: '⚔'};
try { vis = Object.assign(vis, JSON.parse(localStorage.getItem('vis') || '{}')); } catch (e) {}
function visSet(v, save = true) {
  vis = Object.assign(vis, v); const h = document.documentElement;
  h.dataset.theme = vis.tema || 'cinzas';
  if (/^#[0-9a-f]{6}$/i.test(vis.cor || '')) { h.style.setProperty('--gold', vis.cor); h.style.setProperty('--gold-bright', `color-mix(in srgb, ${vis.cor} 70%, #fff)`); }
  else { h.style.removeProperty('--gold'); h.style.removeProperty('--gold-bright'); }
  try { localStorage.setItem('vis', JSON.stringify(vis)); } catch (e) {}
}
function visPanel() {
  let p = $('#vis-panel');
  if (!p) {
    p = document.createElement('div'); p.id = 'vis-panel'; p.className = 'vis-panel'; p.hidden = true;
    p.innerHTML = `<div class="vis-box" role="dialog" aria-label="Personalizar visual"><button class="vis-x" type="button" aria-label="Fechar">×</button><small class="eyebrow">PERSONALIZAR</small><h3>Seu visual</h3>
<h4>Tema</h4><div class="vis-themes">${VIS_TEMAS.map(([id, n, c]) => `<button type="button" data-t="${id}" style="--sw:${c}"><i></i>${n}</button>`).join('')}</div>
<h4>Cor de destaque</h4><div class="vis-row"><input type="color" id="vis-cor" value="#9b78c4"><button type="button" class="secondary" id="vis-cor-reset">Usar cor do tema</button></div>
<h4>Emblema</h4><div class="vis-emb">${VIS_EMB.map(e => `<button type="button" data-e="${e}">${e}</button>`).join('')}</div>
<h4>Frase do perfil</h4><input id="vis-frase" maxlength="80" placeholder="Ex.: Louvado seja o sol!" class="deck-search">
<button class="primary" id="vis-save" type="button">Salvar no meu perfil</button><small class="muted" id="vis-msg"></small></div>`;
    document.body.appendChild(p);
    p.addEventListener('click', (e) => {
      if (e.target === p || e.target.closest('.vis-x')) { p.hidden = true; return; }
      const t = e.target.closest('[data-t]'), em = e.target.closest('[data-e]');
      if (t) visSet({tema: t.dataset.t}); if (em) visSet({emblema: em.dataset.e});
      if (e.target.id === 'vis-cor-reset') visSet({cor: ''});
      if (e.target.id === 'vis-save') visSave();
      visMark();
    });
    $('#vis-cor').addEventListener('input', (e) => { visSet({cor: e.target.value}); visMark(); });
    $('#vis-frase').addEventListener('input', (e) => { vis.frase = e.target.value; });
  }
  $('#vis-frase').value = vis.frase || ''; if (vis.cor) $('#vis-cor').value = vis.cor; visMark(); return p;
}
function visMark() {
  document.querySelectorAll('#vis-panel [data-t]').forEach(b => b.classList.toggle('on', b.dataset.t === vis.tema));
  document.querySelectorAll('#vis-panel [data-e]').forEach(b => b.classList.toggle('on', b.dataset.e === vis.emblema));
}
async function visSave() {
  const msg = $('#vis-msg');
  if (!currentUser) { msg.textContent = 'Aplicado neste navegador. Entre com Discord para salvar no perfil.'; return; }
  try {
    const r = await fetch('/api/hub/prefs', {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({tema: vis.tema, cor: vis.cor || '', frase: vis.frase || '', emblema: vis.emblema})});
    const d = await r.json(); msg.textContent = r.ok ? 'Salvo! Aparece no seu perfil e no ranking.' : (d.error || 'Falha ao salvar.');
    if (r.ok) loadHub();
  } catch (e) { msg.textContent = 'Sem conexão com o servidor.'; }
}
$('#vis-open')?.addEventListener('click', () => { visPanel().hidden = false; });

/* ===== NARABOT PRO · JS visual (sem mexer na lógica do jogo) ===== */
(() => {
  const CB = 'data:image/svg+xml,data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 420 620%22%3E%3Cdefs%3E%3ClinearGradient id=%22g%22 x1=%220%22 y1=%220%22 x2=%221%22 y2=%221%22%3E%3Cstop offset=%220%22 stop-color=%22%23fff3c9%22/%3E%3Cstop offset=%22.55%22 stop-color=%22%23d9ae62%22/%3E%3Cstop offset=%221%22 stop-color=%22%238a6a2e%22/%3E%3C/linearGradient%3E%3ClinearGradient id=%22b%22 x1=%220%22 y1=%220%22 x2=%220%22 y2=%221%22%3E%3Cstop offset=%220%22 stop-color=%22%231d2650%22/%3E%3Cstop offset=%221%22 stop-color=%22%230a0d1c%22/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width=%22420%22 height=%22620%22 fill=%22url(%23b)%22/%3E%3Crect x=%2218%22 y=%2218%22 width=%22384%22 height=%22584%22 rx=%2214%22 fill=%22none%22 stroke=%22url(%23g)%22 stroke-width=%225%22/%3E%3Crect x=%2238%22 y=%2238%22 width=%22344%22 height=%22544%22 rx=%228%22 fill=%22none%22 stroke=%22%23d9ae62%22 stroke-opacity=%22.35%22/%3E%3Ccircle cx=%22210%22 cy=%22310%22 r=%2296%22 fill=%22none%22 stroke=%22url(%23g)%22 stroke-width=%224%22 stroke-dasharray=%228 9%22/%3E%3Cpath d=%22M210 190 230 290 330 310 230 330 210 430 190 330 90 310 190 290z%22 fill=%22url(%23g)%22/%3E%3C/svg%3E', AV = 'data:image/svg+xml,data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 120 120%22%3E%3Crect width=%22120%22 height=%22120%22 fill=%22%23141a33%22/%3E%3Ccircle cx=%2260%22 cy=%2246%22 r=%2222%22 fill=%22%236c86b3%22/%3E%3Cpath d=%22M16 120c0-28 20-44 44-44s44 16 44 44z%22 fill=%22%236c86b3%22/%3E%3C/svg%3E';
  // Imagem quebrada -> arte de reserva (cartas e avatares)
  document.addEventListener('error', (e) => {
    const i = e.target; if (!i || i.tagName !== 'IMG' || i.dataset.fb) return; i.dataset.fb = 1;
    i.src = (i.classList.contains('hub-av') || i.closest('.avatar,.player-chip,.rank-row,.pod')) ? AV : CB;
  }, true);
  // Subtítulo explicativo sob o título de cada aba
  const SUB = {'Início':'Resumo do servidor, seu perfil e a Nara','Comunidade':'Ranking e membros do servidor','Arena':'Desafie um rival e dispute o melhor de três','Deck e Coleção':'Monte seu exército e gerencie suas cartas','Catálogo':'Mods e jogos compartilhados pela comunidade','Mercado e Drops':'Ganhe, abra pacotes e acompanhe recompensas','Ateliê':'Crie a arte oficial das cartas','Meu Portal':'Perfil, santuário, loja, envios e contribuições','Moderação':'Fila de aprovação e notícias','Guia':'Facções, regras e recompensas'};
  const h = document.getElementById('page-title');
  if (h) {
    const p = document.createElement('p'); p.className = 'page-sub'; h.after(p);
    const up = () => { p.textContent = SUB[h.textContent.trim()] || ''; };
    new MutationObserver(up).observe(h, {childList: true, characterData: true, subtree: true}); up();
  }
  // Descrições de rótulo (acessibilidade) nas abas
  document.querySelectorAll('.nav[data-tab]').forEach(b => b.setAttribute('aria-label', (b.querySelector('span') || b).textContent.trim()));
})();

/* ===== NARABOT PRO · Catálogo de jogos e mods ===== */
(() => {
  let kind = 'ports', timer = 0, seq = 0;
  const grid = $('#cat-grid'), cnt = $('#cat-count');
  const safeUrl = (u) => /^https?:\/\//i.test(u || '') ? u : '';
  const card = (it) => {
    // image_url aponta para a rota do portal que serve capas locais do catálogo.
    const img = it.image_url || safeUrl(it.image);
    const tag = kind === 'ports' ? (it.platform || 'Port') : 'Mod';
    const sub = kind === 'ports' ? '' : `<small class="cat-game">${escapeHTML(it.game || '')}</small>`;
    const link = safeUrl(it.link), tut = safeUrl(it.tutorial), iso = safeUrl(it.iso);
    const extras = Array.isArray(it.other_links) ? it.other_links : [];
    const actions = [
      link ? `<a class="primary linkbtn" href="${escapeHTML(link)}" target="_blank" rel="noopener noreferrer">${kind === 'ports' ? 'Baixar' : 'Ver mod'}</a>` : '',
      iso ? `<a class="secondary linkbtn" href="${escapeHTML(iso)}" target="_blank" rel="noopener noreferrer">ISO original</a>` : '',
      tut ? `<a class="secondary linkbtn" href="${escapeHTML(tut)}" target="_blank" rel="noopener noreferrer">Tutorial</a>` : '',
      ...extras.map(x => {
        const url = safeUrl(x.url);
        return url ? `<a class="secondary linkbtn" href="${escapeHTML(url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(x.name || 'Link adicional')}</a>` : '';
      })
    ].filter(Boolean).join('');
    return `<article class="cat-card"><div class="cat-img"${img ? ` style="background-image:url('${escapeHTML(img)}')"` : ''}>${img ? '' : `<span>${escapeHTML((it.name || '?')[0].toUpperCase())}</span>`}<em class="cat-tag">${escapeHTML(tag)}</em></div><div class="cat-body">${sub}<h4>${escapeHTML(it.name || 'Sem nome')}</h4><p>${escapeHTML(it.description || 'Sem descrição.')}</p><div class="cat-actions">${actions}</div></div></article>`;
  };
  async function loadCatalog() {
    const my = ++seq, q = ($('#cat-search').value || '').trim();
    grid.innerHTML = '<p class="muted">Carregando catálogo...</p>';
    try {
      const r = await fetch(`/api/portal/catalog?kind=${kind}&q=${encodeURIComponent(q)}`, {credentials: 'same-origin', cache: 'no-store'});
      const d = await r.json(); if (my !== seq) return;
      if (!r.ok) throw new Error(d.error || 'Falha ao carregar.');
      const items = d.items || [];
      cnt.textContent = `${number(items.length)} ${items.length === 1 ? 'item' : 'itens'}`;
      grid.innerHTML = items.length ? items.map(card).join('') : `<div class="cat-empty"><b>Nada encontrado</b><p class="muted">${q ? 'Tente outra busca.' : 'O catálogo ainda está vazio. Seja o primeiro a sugerir um item!'}</p></div>`;
    } catch (e) { if (my === seq) { cnt.textContent = ''; grid.innerHTML = `<div class="cat-empty"><b>Não foi possível carregar</b><p class="muted">${escapeHTML(e.message)}</p></div>`; } }
  }
  const setKind = (k) => {
    kind = k; document.querySelectorAll('#cat-seg button').forEach(b => b.classList.toggle('on', b.dataset.kind === k));
    $('#cs-plat-l').hidden = k !== 'ports'; $('#cs-name').placeholder = k === 'ports' ? 'Nome do port' : 'Nome do mod'; loadCatalog();
  };
  document.querySelectorAll('#cat-seg button').forEach(b => b.addEventListener('click', () => setKind(b.dataset.kind)));
  $('#cat-search').addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(loadCatalog, 300); });
  document.addEventListener('click', (e) => { if (e.target.closest('[data-tab="catalog"],[data-goto="catalog"]')) loadCatalog(); });
  $('#cs-send').addEventListener('click', async (ev) => {
    const btn = ev.currentTarget, v = (id) => $(id).value.trim();
    const body = {game: v('#cs-game'), name: v('#cs-name'), link: v('#cs-link'), description: v('#cs-desc'), platform: v('#cs-plat') || 'Outra'};
    if (!body.game || !body.name || !/^https?:\/\//i.test(body.link)) return showNotice('Preencha jogo, nome e um link http/https válido.', 'error');
    btn.disabled = true;
    try {
      const r = await fetch(`/api/portal/catalog/${kind}`, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)});
      const d = await r.json().catch(() => ({}));
      if (r.status === 401) return showNotice('Entre com sua conta Discord para sugerir itens.', 'error');
      if (!r.ok) return showNotice(d.error || 'Não foi possível enviar.', 'error');
      showNotice('Sugestão enviada! Ela aparece no catálogo após a aprovação da moderação.', 'success');
      ['#cs-game', '#cs-name', '#cs-link', '#cs-desc', '#cs-plat'].forEach(i => $(i).value = '');
      $('#cat-suggest').open = false;
    } catch (e) { showNotice('Erro de conexão. Tente novamente.', 'error'); } finally { btn.disabled = false; }
  });
})();

/* ===== NARABOT PRO · Portal (perfil, santuário, loja, envios, contribuições, notificações, moderação) ===== */
(() => {
  const E = escapeHTML, $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const ST = {pending: ['Pendente', 'warn'], approved: ['Aprovado', 'ok'], rejected: ['Rejeitado', 'bad'], changes_requested: ['Ajustes pedidos', 'warn']};
  const KIND = {platina: 'Platina', zerado: 'Zerado', run: 'Run Soulslike', ports: 'Port', mods: 'Mod', lore: 'Lore', guide: 'Guia', correction: 'Correção', idea: 'Ideia', faq: 'FAQ', challenge: 'Desafio', game_suggestion: 'Sugestão de jogo'};
  const THEMES = ['Ouro', 'Prata', 'Safira', 'Esmeralda', 'Rubi', 'Ametista'];
  const fdate = (s) => { const d = new Date(String(s || '').replace(' ', 'T')); return isNaN(d) ? '' : d.toLocaleDateString('pt-BR'); };
  const login = '<div class="pt-empty"><b>Entre para continuar</b><p class="muted">Conecte sua conta Discord para usar esta página.</p><a class="primary linkbtn" href="/auth/discord/login">Entrar com Discord</a></div>';
  const empty = (t, s = '') => `<div class="pt-empty"><b>${E(t)}</b>${s ? `<p class="muted">${E(s)}</p>` : ''}</div>`;
  const chip = (st) => { const [t, c] = ST[st] || [st || '—', 'warn']; return `<span class="pt-chip ${c}">${E(t)}</span>`; };
  async function api(path, opt = {}) {
    try {
      const o = {credentials: 'same-origin', cache: 'no-store', ...opt};
      if (opt.json !== undefined) { o.method = o.method || 'POST'; o.headers = {'Content-Type': 'application/json'}; o.body = JSON.stringify(opt.json); delete o.json; }
      const r = await fetch(path, o); let d = null; const t = await r.text();
      try { d = JSON.parse(t); } catch (e) { d = {error: t.slice(0, 160)}; }
      return {ok: r.ok, status: r.status, data: d || {}};
    } catch (e) { return {ok: false, status: 0, data: {error: 'Erro de conexão.'}}; }
  }
  const fail = (r) => showNotice(r.status === 401 ? 'Entre com sua conta Discord.' : (r.data.error || 'Não foi possível concluir.'), 'error');
  const uid = () => currentUser && currentUser.id;
  const field = (l, id, ph = '', ml = 200, cls = '') => `<label class="${cls}">${l}<input id="${id}" maxlength="${ml}" placeholder="${E(ph)}"></label>`;
  const area = (l, id, ph = '', ml = 1000, rows = 4) => `<label class="wide">${l}<textarea id="${id}" rows="${rows}" maxlength="${ml}" placeholder="${E(ph)}"></textarea></label>`;
  const V = (id) => ($('#' + id) || {value: ''}).value.trim();
  let players = null;
  const loadPl = async () => { if (!players) { const r = await api('/api/players'); players = r.ok ? (r.data.players || []) : []; } return players; };
  const nameOf = (id) => ((players || []).find(p => String(p.id) === String(id)) || {}).name || `Membro ${id}`;

  /* ---------- navegação interna ---------- */
  const loaders = {};
  function sub(root, name) {
    $$(`#${root} .pt-pill`).forEach(b => b.classList.toggle('on', b.dataset.p === name));
    $$(`#${root} .pt-pane`).forEach(p => p.hidden = p.dataset.p !== name);
    loaders[name] && loaders[name]();
  }
  $$('.pt-nav').forEach(nav => nav.addEventListener('click', (e) => { const b = e.target.closest('.pt-pill'); if (b) sub(nav.closest('.tab').id, b.dataset.p); }));
  document.addEventListener('click', (e) => {
    const t = e.target.closest('[data-tab="portal"],[data-goto="portal"],[data-tab="admin"]'); if (!t) return;
    const root = (t.dataset.tab || t.dataset.goto) === 'admin' ? 'tab-admin' : 'tab-portal';
    const cur = $$(`#${root} .pt-pill.on`)[0]; sub(root, cur ? cur.dataset.p : $(`#${root} .pt-pill`).dataset.p);
  });

  /* ---------- PERFIL ---------- */
  const THEME_C = {Ouro: ['#d9ae62', 'Brasas douradas'], Prata: ['#c8d2dc', 'Neve de prata'], Safira: ['#5b8def', 'Bolhas do abismo'], Esmeralda: ['#4fcf8a', 'Vaga-lumes'], Rubi: ['#e0463a', 'Chamas rubras'], Ametista: ['#a98bff', 'Estrelas místicas']};
  const LINKS = [['perfil', '🎮', 'Steam / PSN / Xbox'], ['youtube', '▶️', 'YouTube'], ['twitch', '📺', 'Twitch'], ['site', '🌐', 'Site / Portfólio']];
  loaders.profile = async () => {
    const box = $('#pt-profile'); if (!uid()) return box.innerHTML = login;
    const [r, sr] = await Promise.all([api('/api/portal/profile'), api(`/api/portal/sanctuaries/${uid()}`), loadPl()]);
    if (!r.ok) return box.innerHTML = empty('Não foi possível carregar o perfil', r.data.error);
    const p = r.data.profile || {}; let links = {}; try { links = typeof p.links === 'string' ? JSON.parse(p.links || '{}') : (p.links || {}); } catch (e) {}
    const d = sr.ok ? sr.data : {}, s = d.summary || {}, rk = rankOf(s), nm = $('#profile-name').textContent || 'Seu nome';
    const pl = (players || []).find(x => String(x.id) === String(uid())) || {}, pr = PRES[pl.web_online ? 'on' : pl.discord_presence] || PRES.on;
    const num = {platinas: +s.platinas || 0, zerados: +s.zerados || 0, runs: +s.runs || 0, media_nota: +s.media_nota || 0};
    const got = BADGES.filter(b => b[3](num, d));
    const inp = (id, lab, ph, ml, ic) => `<label class="pf-f"><span>${ic ? `<em>${ic}</em>` : ''}${lab}<small class="pf-cnt" data-for="${id}"></small></span><input id="${id}" maxlength="${ml}" placeholder="${E(ph)}" autocomplete="off"></label>`;
    const sw = Object.entries(THEME_C).map(([t, [c, ds]]) => `<button type="button" class="pf-sw" data-t="${t}" style="--c:${c}"><i></i><b>${t}</b><small>${ds}</small></button>`).join('');
    box.innerHTML = `<div class="pf"><div class="pf-grid">
      <aside class="pf-side"><small class="pf-lab">✦ Pré-visualização ao vivo</small>
        <div class="pf-card" id="pf-card"><div class="pf-banner"><div class="pf-rays"></div><div class="pf-temple"></div></div>
          <div class="pf-av"><div class="pf-av-in"><span>${E(nm[0] || '?').toUpperCase()}</span>${pl.avatar ? `<img src="${E(pl.avatar)}" alt="" onerror="this.remove()">` : ''}</div><i class="sx-pres ${pr[0]}"></i></div>
          <div class="pf-body"><div class="pf-nrow"><h3>${E(nm)}</h3><span class="pf-rank">${rk.cur[2]} ${E(rk.cur[1])}</span></div>
            <p class="pf-quote" id="pv-tag"></p>
            <div class="pf-hr"></div><small class="pf-h">SOBRE MIM</small><p class="pf-bio" id="pv-bio"></p>
            <div id="pv-act"></div>
            <small class="pf-h">INSÍGNIAS · ${got.length}/${BADGES.length}</small><div class="pf-bdg">${got.map(b => `<span title="${E(b[1])}">${b[0]}</span>`).join('') || '<em>Jogue, zere e conquiste para ganhar insígnias.</em>'}</div>
            <div id="pv-links" class="pf-lks"></div></div></div>
        <small class="pf-note">É assim que seu santuário aparece para os outros membros.</small></aside>
      <div class="pf-form">
        <section class="pf-sec"><h4><i>1</i>Identidade</h4>${inp('pf-tag', 'Frase de destaque', 'Uma frase que te define', 100, '💬')}${inp('pf-fav', 'Jogo favorito', 'Ex.: Elden Ring', 100, '🎮')}</section>
        <section class="pf-sec"><h4><i>2</i>Tema do santuário</h4><div class="pf-sws">${sw}</div><select id="pf-theme" hidden>${THEMES.map(t => `<option>${t}</option>`).join('')}</select></section>
        <section class="pf-sec"><h4><i>3</i>Inscrições</h4><label class="pf-f"><span><em>📜</em>Biografia<small class="pf-cnt" data-for="pf-bio"></small></span><textarea id="pf-bio" rows="5" maxlength="1000" placeholder="Conte um pouco sobre você e seus jogos..."></textarea></label></section>
        <section class="pf-sec"><h4><i>4</i>Portais</h4><div class="pf-lgrid">${LINKS.map(([k, ic, l]) => inp('pf-l-' + k, l, 'https://...', 250, ic)).join('')}</div><small class="pf-warn" id="pf-warn" hidden>Use links começando com https:// — os outros não aparecem no santuário.</small></section>
      </div></div>
      <div class="pf-bar"><span class="pf-dirty" id="pf-dirty" hidden>● alterações não salvas</span><div class="pt-actions"><button class="primary" id="pf-save" type="button">💾 Salvar perfil</button><button class="secondary" type="button" data-pt-go="sanctuary">🏛 Ver meu santuário</button></div></div></div>`;
    $('#pf-tag').value = p.tagline || ''; $('#pf-fav').value = p.fav_game || ''; $('#pf-bio').value = p.bio || '';
    const th = THEMES.includes(p.theme) ? p.theme : 'Ouro'; $('#pf-theme').value = th;
    LINKS.forEach(([k]) => $('#pf-l-' + k).value = links[k] || '');
    let dirty = false;
    const upd = () => {
      const t = $('#pf-theme').value, card = $('#pf-card'); card.className = `pf-card pt-th-${t}`;
      $$('.pf-sw', box).forEach(b => b.classList.toggle('on', b.dataset.t === t));
      $('#pv-tag').textContent = V('pf-tag') ? `“${V('pf-tag')}”` : 'Escreva uma frase que te define…';
      $('#pv-bio').textContent = V('pf-bio') || 'Sua biografia aparecerá aqui.';
      $('#pv-act').innerHTML = V('pf-fav') ? `<div class="sx-act pf-act"><div class="sx-act-ic">🎮</div><div><small>JOGO FAVORITO</small><b>${E(V('pf-fav'))}</b></div><span class="sx-eq"><i></i><i></i><i></i><i></i></span></div>` : '';
      let bad = false;
      $('#pv-links').innerHTML = LINKS.map(([k, ic, l]) => { const v = V('pf-l-' + k), el = $('#pf-l-' + k); const ok = !v || /^https?:\/\//.test(v); el.classList.toggle('bad', !ok); bad = bad || !ok; return v && ok ? `<span class="sx-portal">${ic} ${l.split(' ')[0]}</span>` : ''; }).join('');
      $('#pf-warn').hidden = !bad;
      $$('.pf-cnt', box).forEach(c => { const el = $('#' + c.dataset.for); c.textContent = `${el.value.length}/${el.maxLength}`; });
      $('#pf-dirty').hidden = !dirty;
    };
    box.querySelector('.pf-form').addEventListener('input', () => { dirty = true; upd(); });
    $$('.pf-sw', box).forEach(b => b.onclick = () => { $('#pf-theme').value = b.dataset.t; dirty = true; upd(); });
    upd(); dirty = false; $('#pf-dirty').hidden = true;
    $('#pf-save').onclick = async () => {
      const l = {}; LINKS.forEach(([k]) => { const v = V('pf-l-' + k); if (v) l[k] = v; });
      const s2 = await api('/api/portal/profile', {json: {tagline: V('pf-tag'), fav_game: V('pf-fav'), bio: V('pf-bio'), theme: $('#pf-theme').value, links: l}});
      if (s2.ok) { showNotice('Perfil salvo com sucesso.', 'success'); dirty = false; upd(); const c = $('#pf-card'); c.classList.add('saved'); setTimeout(() => c.classList.remove('saved'), 1200); } else fail(s2);
    };
  };
  document.addEventListener('click', (e) => { const g = e.target.closest('[data-pt-go]'); if (g) sub('tab-portal', g.dataset.ptGo); });

  /* ---------- SANTUÁRIO ---------- */
  let viewing = null;
  const HON = {respect: ['🛡', 'Respeito'], determination: ['🔥', 'Determinação'], greatness: ['👑', 'Grandeza']};
  /* ---------- SANTUÁRIO · templo, efeitos e render ---------- */
  const RANKS = [[0, 'Peregrino', '🕯'], [8, 'Iniciado', '🗝'], [25, 'Guardião', '🛡'], [60, 'Campeão', '⚔'], [120, 'Lenda', '👑']];
  const rankOf = (s) => {
    const pts = (+s.platinas || 0) * 3 + (+s.zerados || 0) * 2 + (+s.runs || 0); let i = 0;
    RANKS.forEach((r, k) => { if (pts >= r[0]) i = k; });
    const nx = RANKS[i + 1];
    return {pts, i, cur: RANKS[i], nx, pct: nx ? Math.round((pts - RANKS[i][0]) / (nx[0] - RANKS[i][0]) * 100) : 100};
  };
  const templeSVG = () => {
    const cols = [170, 300, 430, 770, 900, 1030].map(x => `<g class="sx-col"><rect x="${x - 34}" y="172" width="68" height="14" rx="2"/><rect x="${x - 26}" y="186" width="52" height="254"/><rect x="${x - 36}" y="440" width="72" height="12" rx="2"/><path class="fl" d="M${x - 13} 190V438M${x} 190V438M${x + 13} 190V438"/></g>`).join('');
    const tri = [...Array(12)].map((_, i) => `<path d="M${130 + i * 82} 138v14"/>`).join('');
    return `<svg class="sx-temple" viewBox="0 0 1200 520" preserveAspectRatio="xMidYMax slice" aria-hidden="true"><defs>
      <linearGradient id="sxStone" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="color-mix(in srgb,var(--tc) 35%,#2a3050)"/><stop offset="1" stop-color="#0a0d1c"/></linearGradient>
      <radialGradient id="sxDoor" cx=".5" cy="1" r=".95"><stop offset="0" stop-color="var(--tc2)" stop-opacity=".95"/><stop offset=".45" stop-color="var(--tc)" stop-opacity=".35"/><stop offset="1" stop-color="#05060d" stop-opacity=".95"/></radialGradient></defs>
      <g fill="url(#sxStone)" stroke="var(--tc)" stroke-opacity=".55" stroke-width="1.5">
      <polygon points="100,122 600,16 1100,122"/><polygon points="170,118 600,30 1030,118" fill="#05060d" fill-opacity=".55"/>
      <rect x="100" y="122" width="1000" height="12"/><rect x="110" y="134" width="980" height="22"/><rect x="110" y="156" width="980" height="16"/>
      ${cols}
      <rect x="120" y="452" width="960" height="18"/><rect x="80" y="470" width="1040" height="20"/><rect x="40" y="490" width="1120" height="30"/></g>
      <g stroke="var(--tc)" stroke-opacity=".5" stroke-width="3" fill="none">${tri}</g>
      <circle class="sx-oculus" cx="600" cy="82" r="18" fill="var(--tc2)"/>
      <path class="sx-doorp" d="M440 452V268Q440 188 600 188Q760 188 760 268V452Z" fill="url(#sxDoor)" stroke="var(--tc2)" stroke-width="2"/>
      <path d="M462 452V272Q462 208 600 208Q738 208 738 272V452" fill="none" stroke="var(--tc2)" stroke-opacity=".5" stroke-width="1.5"/></svg>`;
  };
  const flameHTML = (c) => {
    const f = Math.min(1, .28 + Math.log2(1 + c) / 5).toFixed(2);
    return `<span class="sx-brazier" style="--f:${f}"><i class="sx-fl a"></i><i class="sx-fl b"></i><i class="sx-fl c"></i><i class="sx-bowl"></i><i class="sx-leg"></i></span>`;
  };
  function sxFx(root) {
    const sc = root.querySelector('.sx'); if (!sc) return;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const fmt = (el, v) => { el.textContent = (+v).toFixed(+el.dataset.dec || 0); };
    const countUp = (el) => {
      const n = parseFloat(el.dataset.n); if (isNaN(n)) return;
      if (reduce) return fmt(el, n);
      const t0 = performance.now(), D = 1200;
      const f = (t) => { const k = Math.min(1, (t - t0) / D); fmt(el, n * (1 - Math.pow(1 - k, 3))); if (k < 1) requestAnimationFrame(f); };
      requestAnimationFrame(f);
    };
    const reveal = (el) => { el.classList.add('in'); el.querySelectorAll('[data-n]').forEach(countUp); };
    sc.classList.add('sx-js');
    const io = 'IntersectionObserver' in window ? new IntersectionObserver((es) => es.forEach(e => { if (e.isIntersecting) { reveal(e.target); io.unobserve(e.target); } }), {threshold: .12}) : null;
    sc.querySelectorAll('.sx-rv').forEach(el => io ? io.observe(el) : reveal(el));
    const hero = sc.querySelector('.sx-hero');
    if (hero && !reduce) hero.addEventListener('pointermove', (e) => {
      const r = hero.getBoundingClientRect();
      hero.style.setProperty('--mx', ((e.clientX - r.left) / r.width - .5).toFixed(3));
      hero.style.setProperty('--my', ((e.clientY - r.top) / r.height - .5).toFixed(3));
    });
    const share = sc.querySelector('#sx-share');
    if (share) share.onclick = async () => { try { await navigator.clipboard.writeText(share.dataset.t); showNotice('Cartão copiado! Cole no Discord.', 'success'); } catch (e) { showNotice('Não foi possível copiar.', 'error'); } };
    const av = sc.querySelector('.sx-av');
    sc.querySelectorAll('.pt-honor:not(:disabled)').forEach(b => b.addEventListener('click', () => b.classList.add('lit'), true));
    const cv = sc.querySelector('.sx-embers'); if (!cv || reduce) return;
    const mode = (sc.className.match(/pt-th-(\w+)/) || [])[1] || 'Ouro';
    const CFG = {Ouro: {n: 55, d: -1, sz: [.6, 2.8], sp: [.6, 2.2], k: 'dot'}, Prata: {n: 70, d: 1, sz: [.8, 2.6], sp: [.3, 1], k: 'dot'}, Safira: {n: 28, d: -1, sz: [3, 9], sp: [.4, 1.1], k: 'ring'}, Esmeralda: {n: 38, d: 0, sz: [1.4, 3.2], sp: [.2, .5], k: 'fly'}, Rubi: {n: 80, d: -1, sz: [.8, 3.4], sp: [1.2, 3.2], k: 'dot'}, Ametista: {n: 34, d: 0, sz: [3, 8], sp: [0, 0], k: 'star'}};
    const C = CFG[mode] || CFG.Ouro, rnd = (a, b) => a + Math.random() * (b - a);
    const ctx = cv.getContext('2d'), col = getComputedStyle(sc).getPropertyValue('--tc2').trim() || '#f3d69b';
    let W = 0, H = 0, dpr = 1; const bursts = [];
    const mk = (init) => ({x: Math.random(), y: init ? Math.random() : (C.d > 0 ? -.05 : 1.05), r: rnd(...C.sz), v: rnd(...C.sp) * .0007, s: rnd(0, 6.28), a: rnd(.35, 1)});
    const ps = [...Array(C.n)].map(() => mk(true));
    const burst = () => {
      const a = av.getBoundingClientRect(), c = cv.getBoundingClientRect(); if (!c.width) return;
      const x = (a.left + a.width / 2 - c.left) / c.width, y = (a.top + a.height / 2 - c.top) / c.height;
      for (let i = 0; i < 70; i++) { const g = rnd(0, 6.28), v = rnd(.002, .011); bursts.push({x, y, vx: Math.cos(g) * v, vy: Math.sin(g) * v * 1.3 - .004, l: 1, r: rnd(1, 3.2)}); }
    };
    if (av) av.onclick = () => { av.classList.remove('pop'); void av.offsetWidth; av.classList.add('pop'); burst(); };
    sc._burst = burst;
    const loop = () => {
      if (!cv.isConnected) return;
      if (!document.hidden && cv.clientWidth) {
        dpr = Math.min(2, window.devicePixelRatio || 1);
        if (W !== Math.round(cv.clientWidth * dpr)) { W = cv.width = Math.round(cv.clientWidth * dpr); H = cv.height = Math.round(cv.clientHeight * dpr); }
        ctx.clearRect(0, 0, W, H); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = dpr;
        ps.forEach((p, i) => {
          p.s += C.k === 'star' ? .035 : .02;
          if (C.d) { p.y += C.d * p.v; p.x += Math.sin(p.s) * .0004; if (p.y < -.06 || p.y > 1.06) ps[i] = mk(false); }
          else if (C.k === 'fly') { p.x += Math.cos(p.s * .6 + i) * .0006; p.y += Math.sin(p.s * .5 + i) * .0005; if (p.x < 0 || p.x > 1) p.x = (p.x + 1) % 1; if (p.y < .05 || p.y > .95) p.s += 3; }
          else if (Math.sin(p.s) < -.98) { p.x = Math.random(); p.y = Math.random() * .8; }
          const x = p.x * W, y = p.y * H, r = p.r * dpr, tw = (Math.sin(p.s * (C.k === 'fly' ? 2 : 3)) + 1) / 2;
          if (C.k === 'dot') { ctx.globalAlpha = p.a * Math.max(0, Math.min(1, C.d < 0 ? p.y * 1.6 : (1.1 - p.y))) * (.6 + .4 * tw); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill(); }
          else if (C.k === 'ring') { ctx.globalAlpha = .55 * p.a * Math.min(1, p.y * 2); ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.stroke(); }
          else if (C.k === 'fly') { const g = ctx.createRadialGradient(x, y, 0, x, y, r * 5); g.addColorStop(0, col); g.addColorStop(1, 'transparent'); ctx.globalAlpha = .25 + .75 * tw; ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r * 5, 0, 6.283); ctx.fill(); ctx.fillStyle = col; }
          else { ctx.globalAlpha = tw * p.a; ctx.beginPath(); ctx.moveTo(x, y - r * dpr); ctx.lineTo(x + r * .22 * dpr, y); ctx.lineTo(x, y + r * dpr); ctx.lineTo(x - r * .22 * dpr, y); ctx.closePath(); ctx.moveTo(x - r * dpr, y); ctx.lineTo(x, y + r * .22 * dpr); ctx.lineTo(x + r * dpr, y); ctx.lineTo(x, y - r * .22 * dpr); ctx.closePath(); ctx.fill(); }
        });
        for (let i = bursts.length - 1; i >= 0; i--) {
          const b = bursts[i]; b.x += b.vx; b.y += b.vy; b.vy += .00018; b.l -= .014;
          if (b.l <= 0) { bursts.splice(i, 1); continue; }
          ctx.globalAlpha = b.l; ctx.fillStyle = '#fff6d6'; ctx.beginPath(); ctx.arc(b.x * W, b.y * H, b.r * dpr * b.l, 0, 6.283); ctx.fill();
        }
        ctx.globalAlpha = 1; ctx.fillStyle = col;
      }
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }
  const sxTitle = (t) => `<h4 class="sx-title"><i></i><span>${t}</span><i></i></h4>`;
  const PRES = {online: ['on', 'Online no Discord'], idle: ['idle', 'Ausente'], dnd: ['dnd', 'Não perturbe'], offline: ['off', 'Offline'], on: ['on', 'Online no site']};
  const BADGES = [
    ['🥉', 'Primeira Platina', 'Conquiste 1 platina', (s) => s.platinas >= 1],
    ['🏆', 'Caçador de Platinas', 'Conquiste 10 platinas', (s) => s.platinas >= 10],
    ['💎', 'Lenda das Platinas', 'Conquiste 50 platinas', (s) => s.platinas >= 50],
    ['🎯', 'Zerador Implacável', 'Zere 25 jogos', (s) => s.zerados >= 25],
    ['💀', 'Alma Soulslike', 'Registre 10 runs', (s) => s.runs >= 10],
    ['🔍', 'Olhar Crítico', 'Nota média 8+ com 5 jogos zerados', (s) => s.zerados >= 5 && s.media_nota >= 8],
    ['⭐', 'Estrela do Servidor', 'Tenha 25 seguidores', (s, d) => d.followers >= 25],
    ['🔥', 'Honrado pelos Pares', 'Receba 20 honrarias', (s, d) => Object.values(d.honors || {}).reduce((a, b) => a + (+b || 0), 0) >= 20],
    ['🕯', 'Casa Cheia', 'Receba 5 recados no mural', (s, d) => (d.messages || []).length >= 5]
  ];
  const renderSanctuary = (d, p, s, own, nm, links, sel) => {
    const rk = rankOf(s), pl = (players || []).find(x => String(x.id) === String(viewing)) || {};
    const pr = PRES[pl.web_online ? 'on' : pl.discord_presence] || PRES.offline;
    const num = {platinas: +s.platinas || 0, zerados: +s.zerados || 0, runs: +s.runs || 0, media_nota: +s.media_nota || 0};
    const runes = [['🏆', 'Platinas', s.platinas], ['🎯', 'Zerados', s.zerados], ['⚔', 'Runs', s.runs], ['⭐', 'Nota média', s.media_nota != null ? Number(s.media_nota) : null], ['👥', 'Seguidores', d.followers]]
      .map(([ic, k, v]) => `<div class="sx-rune"><em>${ic}</em><b ${v == null && k === 'Nota média' ? '' : `data-n="${+v || 0}" data-dec="${k === 'Nota média' ? 1 : 0}"`}>${v == null && k === 'Nota média' ? '—' : 0}</b><small>${k}</small></div>`).join('');
    const got = BADGES.map(([ic, t, h, f]) => [ic, t, h, !!f(num, d)]);
    const badges = got.map(([ic, t, h, ok]) => `<div class="sx-badge2 ${ok ? 'ok' : ''}" tabindex="0"><div class="hex"><span>${ok ? ic : '🔒'}</span></div><b>${E(t)}</b><small>${ok ? 'Conquistada' : E(h)}</small></div>`).join('');
    const hon = Object.entries(HON).map(([k, [i, l]]) => { const c = (d.honors || {})[k] || 0; return `<button class="pt-honor sx-altar" data-k="${k}" ${own ? 'disabled' : ''} type="button">${flameHTML(c)}<span class="sx-ic">${i}</span><b>${c}</b><small>${l}</small></button>`; }).join('');
    const lk = Object.entries(links).filter(([, v]) => /^https?:\/\//.test(v)).map(([k, v]) => `<a class="sx-portal" href="${E(v)}" target="_blank" rel="noopener noreferrer">${E(k)} <span>↗</span></a>`).join('');
    const msgs = (d.messages || []).map(m => `<div class="pt-msg sx-offer"><i class="sx-candle"></i><div class="sx-oh"><b>${E(nameOf(m.author_id))}</b><small>${fdate(m.created_at)}</small></div><p>${E(m.message)}</p>${own ? `<button class="text-btn" data-del="${m.id}" type="button">apagar</button>` : ''}</div>`).join('') || '<p class="muted sx-none">Nenhuma oferenda ainda. As velas aguardam o primeiro visitante.</p>';
    const card = `🏛️ **Santuário de ${nm}** — ${rk.cur[2]} ${rk.cur[1]}\n🏆 ${num.platinas} platinas · 🎯 ${num.zerados} zerados · ⚔ ${num.runs} runs${s.media_nota != null ? ` · ⭐ ${num.media_nota.toFixed(1)}` : ''}\n🎖 ${got.filter(g => g[3]).length}/${got.length} insígnias${p.fav_game ? ` · 🎮 ${p.fav_game}` : ''}\n> ${p.tagline || 'Entre no meu santuário!'}\n${location.origin}${location.pathname}`;
    return sel + `<div class="sx pt-th-${E(p.theme || 'Ouro')}">
    <section class="sx-hero">
      <div class="sx-sky"></div><div class="sx-rays"></div><div class="sx-stars"></div>
      ${templeSVG()}<canvas class="sx-embers"></canvas>
      <div class="sx-core">
        <small class="sx-eyebrow">${own ? '✦ SEU SANTUÁRIO ✦' : '✦ SANTUÁRIO ✦'}</small>
        <div class="sx-av" title="Clique!"><svg viewBox="0 0 200 200" aria-hidden="true"><circle class="r1" cx="100" cy="100" r="96"/><circle class="r2" cx="100" cy="100" r="86"/></svg><div class="sx-av-in"><span>${E(nm[0] || '?').toUpperCase()}</span>${pl.avatar ? `<img src="${E(pl.avatar)}" alt="" onerror="this.remove()">` : ''}</div><span class="sx-badge">${rk.cur[2]}</span><i class="sx-pres ${pr[0]}" title="${pr[1]}"></i></div>
        <div class="sx-rank">${E(rk.cur[1])}</div>
        <h3 class="sx-name">${E(nm)}</h3>
        <p class="sx-tag">“${E(p.tagline || 'Este jogador ainda não escreveu uma frase.')}”</p>
        <div class="sx-chips"><span class="sx-chip pres ${pr[0]}">${pr[1]}</span><span class="sx-chip">${rk.pts} pontos de glória</span><span class="sx-chip">🎖 ${got.filter(g => g[3]).length}/${got.length} insígnias</span></div>
        ${p.fav_game ? `<div class="sx-act"><div class="sx-act-ic">🎮</div><div><small>JOGO FAVORITO</small><b>${E(p.fav_game)}</b></div><span class="sx-eq"><i></i><i></i><i></i><i></i></span></div>` : ''}
        <div class="sx-lvl" title="${rk.nx ? `Faltam ${rk.nx[0] - rk.pts} pontos para ${E(rk.nx[1])}` : 'Nível máximo'}"><div><i style="width:${rk.pct}%"></i></div><small>${rk.nx ? `Próximo título: ${E(rk.nx[1])}` : 'Título máximo alcançado'}</small></div>
        <div class="sx-btns">${own ? '' : '<button class="primary sx-follow" id="sc-follow" type="button">Seguir</button>'}<button class="secondary sx-sharebtn" id="sx-share" type="button" data-t="${E(card)}">📋 Copiar para o Discord</button></div>
      </div>
    </section>
    <div class="sx-rv">${sxTitle('Runas de Conquista')}<div class="sx-runes">${runes}</div></div>
    <div class="sx-rv">${sxTitle('Salão de Insígnias')}<div class="sx-badges">${badges}</div></div>
    <div class="sx-rv">${sxTitle('Altares de Honra')}<div class="sx-altars pt-honors">${hon}</div>${own ? '' : '<small class="muted sx-hint">Acenda uma chama: você pode honrar este jogador uma vez por semana.</small>'}</div>
    <div class="sx-rv">${sxTitle('Inscrições')}<div class="sx-tablet"><p class="sx-bio">${E(p.bio || 'Nenhuma inscrição foi gravada nesta pedra.')}</p>${lk ? `<div class="sx-portals">${lk}</div>` : ''}</div></div>
    <div class="sx-rv">${sxTitle('Mural de Oferendas')}<div class="sx-offers pt-msgs">${msgs}</div>${own ? '' : `<div class="pt-form sx-leave"><label class="wide">Deixe uma oferenda<textarea id="gb-text" rows="2" maxlength="300" placeholder="Até 300 caracteres. Um recado por dia."></textarea></label><button class="primary" id="gb-send" type="button">Acender uma vela</button></div>`}</div>
    </div>`;
  };

  loaders.sanctuary = async (target) => {
    const box = $('#pt-sanctuary'); if (!uid()) return box.innerHTML = login;
    await loadPl(); viewing = String(target || viewing || uid());
    const r = await api(`/api/portal/sanctuaries/${viewing}`);
    const sel = `<div class="pt-pick"><input id="sc-search" class="deck-search" type="search" placeholder="Visitar o santuário de outro membro..." list="sc-list" autocomplete="off"><datalist id="sc-list">${players.slice(0, 200).map(p => `<option value="${E(p.name)}"></option>`).join('')}</datalist><button class="secondary" id="sc-go" type="button">Visitar</button>${viewing !== String(uid()) ? '<button class="secondary" id="sc-me" type="button">Meu santuário</button>' : ''}</div>`;
    if (!r.ok) { box.innerHTML = sel + empty('Santuário indisponível', r.data.error); }
    else {
      const d = r.data, p = d.profile || {}, s = d.summary || {}, own = d.is_owner; let links = {}; try { links = typeof p.links === 'string' ? JSON.parse(p.links || '{}') : (p.links || {}); } catch (e) {}
      const nm = own ? ($('#profile-name').textContent || 'Seu santuário') : nameOf(viewing);
      box.innerHTML = renderSanctuary(d, p, s, own, nm, links, sel); sxFx(box);
      $$('.pt-honor', box).forEach(b => b.onclick = async () => { const x = await api('/api/portal/sanctuaries/honor', {json: {user_id: Number(viewing), honor_key: b.dataset.k}}); x.ok ? (showNotice('Honraria enviada!', 'success'), loaders.sanctuary()) : fail(x); });
      const fo = $('#sc-follow'); if (fo) fo.onclick = async () => { const x = await api('/api/portal/community/follow', {json: {user_id: Number(viewing)}}); x.ok ? (showNotice(x.data.following ? 'Agora você segue este jogador.' : 'Você deixou de seguir.', 'success'), loaders.sanctuary()) : fail(x); };
      const gs = $('#gb-send'); if (gs) gs.onclick = async () => { const x = await api(`/api/portal/sanctuaries/${viewing}/guestbook`, {json: {message: V('gb-text')}}); x.ok ? (showNotice('Recado enviado.', 'success'), loaders.sanctuary()) : fail(x); };
      $$('[data-del]', box).forEach(b => b.onclick = async () => { const x = await api(`/api/portal/sanctuaries/${viewing}/guestbook?id=${b.dataset.del}`, {method: 'DELETE'}); x.ok ? loaders.sanctuary() : fail(x); });
    }
    const go = $('#sc-go'); if (go) go.onclick = () => { const q = V('sc-search').toLowerCase(), p = players.find(x => x.name.toLowerCase() === q) || players.find(x => x.name.toLowerCase().includes(q)); p ? loaders.sanctuary(p.id) : showNotice('Membro não encontrado.', 'error'); };
    const me = $('#sc-me'); if (me) me.onclick = () => loaders.sanctuary(uid());
  };

  /* ---------- LOJA ---------- */
  const TYPES = {};
  loaders.store = async () => {
    const box = $('#pt-store'); if (!uid()) return box.innerHTML = login;
    const r = await api('/api/portal/store'); if (!r.ok) return box.innerHTML = empty('Loja indisponível', r.data.error);
    const items = r.data.items || [], groups = {}; items.forEach(i => (groups[i.type] = groups[i.type] || []).push(i));
    const card = (i) => `<article class="pt-item ${i.equipped ? 'eq' : ''}"><div class="pt-emoji">${E(i.emoji || '🎁')}</div><h4>${E(i.name)}</h4><p>${E(i.description || '')}</p><div class="pt-meta"><span class="pt-chip">◈ ${number(i.price)}</span>${i.min_level > 1 ? `<span class="pt-chip warn">Nível ${i.min_level}+</span>` : ''}${i.owned ? '<span class="pt-chip ok">Seu</span>' : ''}</div>
      ${i.owned ? `<button class="secondary" data-a="${i.equipped ? 'unequip' : 'equip'}" data-i="${E(i.id)}" type="button">${i.equipped ? 'Desequipar' : 'Equipar'}</button>` : `<button class="primary" data-a="buy" data-i="${E(i.id)}" type="button">Comprar</button>`}</article>`;
    box.innerHTML = `<div class="pt-balance"><span>Seu saldo</span><b>◈ ${number(r.data.balance)}</b><small class="muted">Denários</small></div>` + (Object.entries(groups).map(([t, l]) => `<h4 class="pt-gt">${E(t)}</h4><div class="pt-store">${l.map(card).join('')}</div>`).join('') || empty('A loja está vazia'));
    $$('[data-a]', box).forEach(b => b.onclick = async () => { b.disabled = true; const x = await api('/api/portal/store/action', {json: {item: b.dataset.i, action: b.dataset.a}}); x.ok ? (showNotice(b.dataset.a === 'buy' ? 'Compra realizada!' : 'Atualizado.', 'success'), loaders.store(), loadAccount && 0) : (fail(x), b.disabled = false); });
  };

  /* ---------- ENVIOS (platina, zerado, run) ---------- */
  let sKind = 'platina', runOpts = null;
  const num = (id, l, mn, mx) => `<label>${l}<input id="${id}" type="number" min="${mn}" max="${mx}" placeholder="${mn}–${mx}"></label>`;
  function sForm() {
    const box = $('#pt-form'), run = sKind === 'run';
    const g = run ? `<label>Jogo<select id="sf-gid"><option value="">Selecione...</option>${(runOpts.games || []).map(x => `<option value="${x.id}">${E(x.name)}</option>`).join('')}</select></label><label>Desafio<select id="sf-cid"><option value="">Selecione...</option></select></label><label>Tempo (min)<input id="sf-min" type="number" min="1" placeholder="Ex.: 90"></label>${field('Build / estilo', 'sf-build', 'Opcional', 300)}`
      : `${field('Jogo', 'sf-game', 'Nome do jogo', 100)}${field('Plataforma', 'sf-plat', 'PC, PS5, Switch...', 40)}<label>${sKind === 'platina' ? 'Data da platina' : 'Data de conclusão'}<input id="sf-date" type="date"></label>`;
    box.innerHTML = `<div class="pt-form">${g}${num('sf-rate', 'Nota (opcional)', 1, 10)}${num('sf-diff', 'Dificuldade (opcional)', 1, 5)}${area('Comentário', 'sf-com', 'Algo para a moderação ou para a comunidade...', 500, 3)}<label class="wide">Comprovantes (até 5 imagens/vídeos)<input id="sf-files" type="file" multiple accept="image/*,video/*"></label><button class="primary" id="sf-send" type="button">Enviar para aprovação</button></div>`;
    if (run) $('#sf-gid').onchange = () => { const gid = Number($('#sf-gid').value); $('#sf-cid').innerHTML = '<option value="">Selecione...</option>' + (runOpts.challenges || []).filter(c => !c.game_id || c.game_id === gid).map(c => `<option value="${c.id}">${E(c.name)}</option>`).join(''); };
    $('#sf-send').onclick = async (ev) => {
      const fd = new FormData(), files = [...$('#sf-files').files].slice(0, 5);
      if (!files.length) return showNotice('Anexe ao menos um comprovante.', 'error');
      if (run) { const m = Number(V('sf-min')); fd.append('game_id', V('sf-gid')); fd.append('challenge_id', V('sf-cid')); fd.append('seconds', Math.round(m * 60)); fd.append('build', V('sf-build')); }
      else { fd.append('game', V('sf-game')); fd.append('platform', V('sf-plat')); fd.append('date', V('sf-date')); }
      fd.append('rating', V('sf-rate')); fd.append('difficulty', V('sf-diff')); fd.append('comment', V('sf-com')); files.forEach(f => fd.append('proofs', f));
      ev.currentTarget.disabled = true;
      const x = await api(run ? '/api/portal/runs' : `/api/portal/submit/${sKind}`, {method: 'POST', body: fd});
      $('#sf-send') && ($('#sf-send').disabled = false);
      if (x.ok) { showNotice('Envio registrado! Aguarde a aprovação da moderação.', 'success'); sForm(); loadMine(); } else fail(x);
    };
  }
  async function loadMine() {
    const box = $('#pt-mine'), r = await api('/api/portal/mine'); if (!r.ok) return box.innerHTML = '';
    const rows = (r.data.items || []).map(i => `<div class="pt-row"><span class="pt-chip">${E(KIND[i.kind] || i.kind)}</span><div><b>${E(i.game)}</b><small>${E(i.platform || '')} ${i.date ? '· ' + E(i.date) : ''}</small>${i.comment && i.status !== 'pending' ? `<small class="muted">${E(i.comment)}</small>` : ''}</div>${chip(i.status)}${i.status === 'pending' ? `<button class="text-btn" data-c="${i.kind}/${i.id}" type="button">cancelar</button>` : ''}</div>`).join('');
    box.innerHTML = `<h4 class="pt-gt">Meus envios</h4>${rows || empty('Você ainda não enviou nada', 'Seus envios e o status da aprovação aparecem aqui.')}`;
    $$('[data-c]', box).forEach(b => b.onclick = async () => { if (!confirm('Cancelar este envio?')) return; const x = await api(`/api/portal/mine/${b.dataset.c}`, {method: 'DELETE'}); x.ok ? loadMine() : fail(x); });
  }
  loaders.submit = async () => {
    const box = $('#pt-submit-body'); if (!uid()) { box.hidden = true; $('#pt-submit-login').innerHTML = login; return; }
    box.hidden = false; $('#pt-submit-login').innerHTML = '';
    if (!runOpts) { const r = await api('/api/portal/runs/options'); runOpts = r.ok ? r.data : {games: [], challenges: []}; }
    sForm(); loadMine();
  };
  $('#pt-kind').addEventListener('click', (e) => { const b = e.target.closest('button'); if (!b) return; sKind = b.dataset.k; $$('#pt-kind button').forEach(x => x.classList.toggle('on', x === b)); sForm(); });

  /* ---------- CONTRIBUIÇÕES ---------- */
  let cFilter = 'approved';
  const CK = ['guide', 'lore', 'idea', 'faq', 'correction', 'challenge', 'game_suggestion', 'run'];
  loaders.contrib = async () => {
    const box = $('#pt-contrib-list'); $$('#pt-cfilter button').forEach(b => b.classList.toggle('on', b.dataset.f === cFilter));
    await loadPl();
    let r; if (cFilter === 'fav') r = uid() ? await api('/api/portal/community/favorites') : {ok: false, status: 401, data: {}}; else r = await api(`/api/portal/contributions?${cFilter === 'mine' ? 'mine=1' : 'status=approved'}`);
    if (r.status === 401) return box.innerHTML = login; if (!r.ok) return box.innerHTML = empty('Não foi possível carregar', r.data.error);
    const items = r.data.items || [];
    box.innerHTML = items.map(c => c.title === undefined ? `<div class="pt-card"><small class="muted">Item salvo #${E(c.target_id)}</small></div>` : `<article class="pt-card pt-post"><div class="pt-meta"><span class="pt-chip">${E(KIND[c.kind] || c.kind)}</span>${c.game_name ? `<span class="pt-chip ok">${E(c.game_name)}</span>` : ''}${cFilter === 'mine' ? chip(c.status) : ''}<small class="muted">${E(nameOf(c.user_id))} · ${fdate(c.created_at)}</small></div><h4>${E(c.title)}</h4><p>${E(c.summary || String(c.content || '').slice(0, 220))}</p><div class="pt-actions">${[['like', '👍', 'Curtir'], ['useful', '💡', 'Útil'], ['respect', '🤝', 'Respeito']].map(([k, i, l]) => `<button class="secondary" data-r="${k}" data-id="${c.id}" title="${l}" type="button">${i} ${l}</button>`).join('')}<button class="secondary" data-bm="${c.id}" type="button">🔖 Salvar</button>${c.kind === 'challenge' && c.status === 'approved' ? `<button class="primary" data-j="${c.id}" type="button">⚔ Participar</button>` : ''}</div></article>`).join('') || empty('Nada por aqui ainda', cFilter === 'mine' ? 'Você ainda não enviou contribuições.' : 'Seja o primeiro a contribuir!');
    $$('[data-r]', box).forEach(b => b.onclick = async () => { const x = await api('/api/portal/community/interact', {json: {target_type: 'contribution', target_id: Number(b.dataset.id), reaction: b.dataset.r}}); x.ok ? showNotice(x.data.added ? 'Reação registrada.' : 'Reação removida.', 'success') : fail(x); });
    $$('[data-bm]', box).forEach(b => b.onclick = async () => { const x = await api('/api/portal/community/bookmark', {json: {target_type: 'contribution', target_id: Number(b.dataset.bm)}}); x.ok ? showNotice(x.data.saved ? 'Salvo nos favoritos.' : 'Removido dos favoritos.', 'success') : fail(x); });
    $$('[data-j]', box).forEach(b => b.onclick = async () => { const x = await api('/api/portal/community/challenge', {json: {contribution_id: Number(b.dataset.j), action: 'join'}}); x.ok ? showNotice('Participação atualizada.', 'success') : fail(x); });
  };
  $('#pt-cfilter').addEventListener('click', (e) => { const b = e.target.closest('button'); if (b) { cFilter = b.dataset.f; loaders.contrib(); } });
  $('#pt-cform').innerHTML = `<div class="pt-form"><label>Tipo<select id="cf-kind">${CK.map(k => `<option value="${k}">${KIND[k]}</option>`).join('')}</select></label>${field('Jogo (opcional)', 'cf-game', 'Nome do jogo', 100)}${field('Título', 'cf-title', 'Título da contribuição', 120, 'wide')}${field('Resumo', 'cf-sum', 'Em uma frase', 500, 'wide')}${area('Conteúdo (mín. 20 caracteres)', 'cf-content', 'Escreva seu guia, lore, ideia...', 12000, 7)}${field('Fontes (opcional)', 'cf-src', 'Links ou referências', 1500, 'wide')}<button class="primary" id="cf-send" type="button">Enviar contribuição</button><small class="muted">Passa pela moderação antes de aparecer para todos.</small></div>`;
  $('#cf-send').onclick = async () => {
    const x = await api('/api/portal/contributions', {json: {kind: $('#cf-kind').value, game_name: V('cf-game'), title: V('cf-title'), summary: V('cf-sum'), content: V('cf-content'), sources: V('cf-src')}});
    if (x.ok) { showNotice('Contribuição enviada para aprovação!', 'success'); ['cf-game', 'cf-title', 'cf-sum', 'cf-content', 'cf-src'].forEach(i => $('#' + i).value = ''); cFilter = 'mine'; loaders.contrib(); } else fail(x);
  };

  /* ---------- NOTIFICAÇÕES ---------- */
  const NP = {approvals: 'Aprovações', rejections: 'Rejeições', levels: 'Subidas de nível', replies: 'Respostas', challenges: 'Desafios'};
  loaders.notif = async () => {
    const box = $('#pt-notif'); if (!uid()) return box.innerHTML = login;
    const r = await api('/api/portal/notifications'); if (!r.ok) return box.innerHTML = empty('Não foi possível carregar', r.data.error);
    const items = r.data.items || [], pr = r.data.preferences || {};
    box.innerHTML = `<div class="pt-grid2"><div class="pt-card"><div class="pt-head"><h4>Não lidas</h4>${items.length ? '<button class="text-btn" id="nt-all" type="button">Marcar todas como lidas</button>' : ''}</div>${items.map(n => `<div class="pt-row"><span class="pt-chip">${E(NP[n.category] || n.category || 'Aviso')}</span><div><b>${E(n.message)}</b><small>${fdate(n.created_at)}</small></div></div>`).join('') || empty('Tudo em dia', 'Você não tem notificações novas.')}</div>
    <div class="pt-card"><h4>O que você quer receber</h4>${Object.entries(NP).map(([k, l]) => `<label class="pt-switch"><span>${l}</span><input type="checkbox" data-k="${k}" ${pr[k] !== false ? 'checked' : ''}><i></i></label>`).join('')}</div></div>`;
    const all = $('#nt-all'); if (all) all.onclick = async () => { const x = await api('/api/portal/notifications', {json: {action: 'read_all'}}); x.ok ? loaders.notif() : fail(x); };
    $$('[data-k]', box).forEach(c => c.onchange = async () => { const x = await api('/api/portal/notifications', {json: {key: c.dataset.k, enabled: c.checked}}); x.ok ? showNotice('Preferência salva.', 'success') : (fail(x), c.checked = !c.checked); });
  };

  /* ---------- MODERAÇÃO ---------- */
  const isCatalog = (i) => i.kind === 'ports' || i.kind === 'mods';
  const isContrib = (i) => 'guild_id' in i || ('content' in i && 'title' in i);
  loaders.queue = async () => {
    const box = $('#ad-queue'); await loadPl();
    const r = await api('/api/portal/admin/queue'); if (!r.ok) return box.innerHTML = empty('Acesso restrito à moderação', r.data.error);
    const items = r.data.items || [];
    box.innerHTML = `<div class="pt-balance"><span>Na fila</span><b>${items.length}</b><small class="muted">itens aguardando revisão</small></div>` + (items.map(i => {
      const k = isContrib(i) ? 'contribution' : i.kind, title = i.title || i.game || i.name || '—', extra = i.challenge ? ` · ${i.challenge}` : i.platform ? ` · ${i.platform}` : '';
      const proofs = (i.proofs || []).concat(i.proof_url ? [{url: i.proof_url, filename: 'Comprovante'}] : []).filter(p => /^https?:\/\/|^\//.test(p.url || '')).map(p => `<a href="${E(p.url)}" target="_blank" rel="noopener noreferrer">${E(p.filename || 'Comprovante')}</a>`).join('');
      return `<div class="pt-card pt-q" data-k="${k}" data-id="${i.id}"><div class="pt-meta"><span class="pt-chip">${E(KIND[isContrib(i) ? 'guide' : i.kind] && !isContrib(i) ? KIND[i.kind] : (isContrib(i) ? 'Contribuição · ' + (KIND[i.kind] || i.kind) : i.kind))}</span><small class="muted">${E(nameOf(i.user_id || i.autor_id))} · ${fdate(i.created_at)}</small></div><h4>${E(title)}<small>${E(extra)}</small></h4>${i.summary || i.comment || i.build ? `<p class="muted">${E(i.summary || i.comment || i.build)}</p>` : ''}${proofs ? `<div class="pt-proofs">${proofs}</div>` : ''}<div class="pt-actions"><button class="primary" data-d="approved" type="button">Aprovar</button><button class="secondary" data-d="rejected" type="button">Rejeitar</button>${isCatalog(i) ? '' : '<button class="secondary" data-d="changes_requested" type="button">Pedir ajustes</button>'}</div></div>`;
    }).join('') || empty('Fila vazia', 'Nenhum item aguardando aprovação.'));
    $$('.pt-q [data-d]', box).forEach(b => b.onclick = async () => {
      const q = b.closest('.pt-q'), k = q.dataset.k, a = b.dataset.d; let note = '';
      if (a !== 'approved' && !isCatalog({kind: k})) { note = prompt('Observação para o membro (opcional):') || ''; }
      b.disabled = true;
      const x = isCatalog({kind: k}) ? await api(`/api/portal/catalog/${k}/${q.dataset.id}`, {json: {action: a}}) : await api(`/api/portal/admin/${k}/${q.dataset.id}`, {json: {action: a, note}});
      x.ok ? (showNotice('Decisão registrada.', 'success'), loaders.queue()) : (fail(x), b.disabled = false);
    });
  };
  loaders.news = async () => {
    const box = $('#ad-news'), r = await api('/api/portal/admin/news'); if (!r.ok) return box.innerHTML = empty('Acesso restrito à moderação', r.data.error);
    box.innerHTML = `<div class="pt-grid2"><div class="pt-card"><h4>Feeds monitorados</h4>${(r.data.feeds || []).map(f => `<div class="pt-row"><span class="pt-chip ${f.ativo ? 'ok' : 'warn'}">${f.ativo ? 'Ativo' : 'Pausado'}</span><div><b>${E(f.nome)}</b><small>${E(f.url)}</small></div><button class="text-btn" data-rm="${f.id}" type="button">remover</button></div>`).join('') || empty('Nenhum feed cadastrado')}</div><div class="pt-card"><h4>Adicionar feed RSS</h4><div class="pt-form">${field('Nome', 'nw-name', 'Ex.: IGN Brasil', 80, 'wide')}${field('URL do RSS (https)', 'nw-url', 'https://...', 500, 'wide')}<button class="primary" id="nw-add" type="button">Validar e adicionar</button><small class="muted">As notícias novas são publicadas pelo bot no canal configurado.</small></div></div></div>`;
    $('#nw-add').onclick = async (ev) => { ev.currentTarget.disabled = true; const x = await api('/api/portal/admin/news', {json: {action: 'add', name: V('nw-name'), url: V('nw-url')}}); x.ok ? (showNotice('Feed adicionado.', 'success'), loaders.news()) : (fail(x), $('#nw-add').disabled = false); };
    $$('[data-rm]', box).forEach(b => b.onclick = async () => { if (!confirm('Remover este feed?')) return; const x = await api('/api/portal/admin/news', {json: {action: 'remove', id: Number(b.dataset.rm)}}); x.ok ? loaders.news() : fail(x); });
  };

  /* ---------- Descobrir moderador (mostra a aba Moderação) ---------- */
  (async () => { await new Promise(r => setTimeout(r, 1200)); if (!uid()) return; const r = await api('/api/portal/admin/queue'); if (r.ok) { const n = $('#nav-admin'); if (n) n.hidden = false; } })();
  window.portalVisit = (id) => { document.querySelector('.nav[data-tab="portal"]').click(); setTimeout(() => sub('tab-portal', 'sanctuary') || loaders.sanctuary(id), 50); };
})();


// Recalcula a largura ótima das cartas quando o jogador redimensiona a janela.
window.addEventListener('resize', () => {
  const nextWidth = window.innerWidth;
  if (!currentGwentMatch || Math.abs(nextWidth - gwentLastViewportWidth) < 80) return;
  gwentLastViewportWidth = nextWidth;
  refreshGwentMatch();
}, {passive:true});


/* V20 — Arsenal de Relíquias: pré-seleção persistida no navegador. */
(() => {
  const relics = {
    reliquia_grande_runa_godrick: ['Grande Runa de Godrick','Lendária','Concede +1 de bônus a todas as unidades aliadas em campo.','Grande Runa'],
    reliquia_runa_nao_nascidos: ['Grande Runa dos Não Nascidos','Lendária','Purifica Geada e Podridão dos aliados e fortalece os purificados.','Grande Runa'],
    reliquia_runa_morte: ['Runa da Morte','Mítica','Corrói bônus positivos das unidades inimigas em cada fileira.','Grande Runa'],
    reliquia_noite_chama: ['Espada da Noite e da Chama','Lendária','Escolha entre a postura da Chama ou da Noite para atacar uma fileira inimiga.','Arma lendária'],
    reliquia_lamina_negra: ['Lâmina Negra','Mítica','Reduz o bônus de uma unidade inimiga; Escudo pode bloquear o golpe.','Arma lendária'],
    reliquia_algemas_margit: ['Algemas de Margit','Épica','Anula os bônus positivos de uma unidade inimiga.','Artefato']
  };
  const select = document.querySelector('#gwent-relic-select');
  const preview = document.querySelector('#gwent-relic-preview');
  const status = document.querySelector('#gwent-relic-status');
  if (!select || !preview) return;
  const render = () => {
    const relic = relics[select.value];
    preview.innerHTML = relic
      ? `<div class="v52-relic-seal"><i>♜</i><span>${escapeHTML(relic[3])}</span></div><small>${escapeHTML(relic[1])} · ${escapeHTML(relic[3])}</small><b>${escapeHTML(relic[0])}</b><p>${escapeHTML(relic[2])}</p><span class="gwent-relic-equipped">PREPARADA</span>`
      : '<b>Nenhuma Relíquia selecionada</b><p>Você entrará sem Relíquia equipada.</p>';
    if (status) status.textContent = relic ? 'Carta possuída. Salve o deck para equipar esta Relíquia. Chance de Relíquia: 0,50% por drop.' : 'Somente cartas de Relíquia que você possui podem ser equipadas. Chance de drop: 0,50% por carta.';
  };
  render();
  select.addEventListener('change', () => {
    render();
    if (typeof renderGwentBuilder === 'function') renderGwentBuilder();
  });
})();
