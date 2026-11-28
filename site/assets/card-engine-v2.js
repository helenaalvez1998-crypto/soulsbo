(() => {
  'use strict';

  const $ = (id) => document.getElementById(id);
  const app = {
    data: null,
    inventory: new Map(),
    cards: new Map(),
    decks: [],
    matches: [],
    editor: { deckId: null, version: null, selected: [], name: '', leaderId: '' },
    activeMatch: null,
    pollTimer: null,
    pendingChoice: null,
  };

  const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (ch) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  })[ch]);
  const notify = (message, success = false) => {
    const node = $('ce-alert');
    node.textContent = message;
    node.className = `ce-alert${success ? ' success' : ''}`;
    node.hidden = false;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };
  const clearNotify = () => { $('ce-alert').hidden = true; };

  async function api(path, options = {}) {
    const config = { credentials: 'same-origin', cache: 'no-store', ...options };
    config.headers = { ...(options.headers || {}) };
    if (options.body && typeof options.body !== 'string') {
      config.headers['Content-Type'] = 'application/json';
      config.body = JSON.stringify(options.body);
    }
    const response = await fetch(path, config);
    let body = {};
    try { body = await response.json(); } catch (_) { /* empty response */ }
    if (!response.ok) {
      const error = new Error(body.error || `Falha HTTP ${response.status}`);
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function resetEditor() {
    app.editor = { deckId: null, version: null, selected: [], name: '', leaderId: '' };
    $('ce-deck-name').value = '';
    $('ce-leader').value = '';
    $('ce-cancel-edit').hidden = true;
    $('ce-save-deck').textContent = 'Salvar deck';
    renderBuilder();
  }

  function renderLeaders() {
    const select = $('ce-leader');
    select.innerHTML = '<option value="">Selecione um líder</option>' + app.data.leaders.map((leader) =>
      `<option value="${esc(leader.leader_id)}">${esc(leader.name)} · ${esc(leader.faction_id)} · ${leader.energy_cost ?? '—'} energia</option>`
    ).join('');
  }

  function copyCounts() {
    const counts = new Map();
    for (const exemplarId of app.editor.selected) {
      const item = app.inventory.get(Number(exemplarId));
      if (!item) continue;
      counts.set(item.card_id, (counts.get(item.card_id) || 0) + 1);
    }
    return counts;
  }

  function renderInventory() {
    const container = $('ce-inventory');
    const filter = $('ce-card-filter').value.trim().toLocaleLowerCase('pt-BR');
    const selected = new Set(app.editor.selected.map(Number));
    const counts = copyCounts();
    const items = [...app.inventory.values()].filter((item) => {
      if (selected.has(Number(item.exemplar_id))) return false;
      return !filter || `${item.name} ${item.card_id} ${item.rarity}`.toLocaleLowerCase('pt-BR').includes(filter);
    });
    if (!items.length) {
      container.innerHTML = '<p class="ce-empty">Nenhum exemplar disponível com esse filtro.</p>';
      return;
    }
    container.innerHTML = items.map((item) => {
      const count = counts.get(item.card_id) || 0;
      const disabled = app.editor.selected.length >= 30 || count >= 3;
      const power = item.power == null ? 'poder —' : `poder ${item.power}`;
      return `<div class="ce-card-row">
        <div class="ce-card-info"><strong>${esc(item.name)}</strong><small>${esc(item.rarity || 'Sem raridade')} · ${esc(power)} · ${item.energy_cost ?? '—'} energia · exemplar #${item.exemplar_id}</small></div>
        <button class="ce-button ce-ghost" data-add="${item.exemplar_id}" ${disabled ? 'disabled' : ''}>Adicionar</button>
      </div>`;
    }).join('');
    container.querySelectorAll('[data-add]').forEach((button) => {
      button.addEventListener('click', () => {
        const id = Number(button.dataset.add);
        const item = app.inventory.get(id);
        if (!item || app.editor.selected.length >= 30) return;
        const countsNow = copyCounts();
        if ((countsNow.get(item.card_id) || 0) >= 3) return notify('O limite é de três cópias por modelo.');
        app.editor.selected.push(id);
        renderBuilder();
      });
    });
  }

  function renderSelected() {
    const container = $('ce-selected');
    if (!app.editor.selected.length) {
      container.innerHTML = '<p class="ce-muted">Adicione exemplares da sua coleção.</p>';
      return;
    }
    container.innerHTML = app.editor.selected.map((id, index) => {
      const item = app.inventory.get(Number(id));
      return `<div class="ce-selected-row"><div class="ce-card-info"><strong>${esc(item?.name || `Exemplar #${id}`)}</strong><small>Slot ${index + 1} · exemplar #${id}</small></div><button class="ce-button ce-ghost" data-remove="${id}" aria-label="Remover exemplar">Remover</button></div>`;
    }).join('');
    container.querySelectorAll('[data-remove]').forEach((button) => {
      button.addEventListener('click', () => {
        app.editor.selected = app.editor.selected.filter((id) => Number(id) !== Number(button.dataset.remove));
        renderBuilder();
      });
    });
  }

  function renderBuilder() {
    const count = app.editor.selected.length;
    $('ce-deck-counter').textContent = `${count} / 30`;
    $('ce-deck-counter').classList.toggle('complete', count === 30);
    const counts = copyCounts();
    $('ce-copy-counter').textContent = `${counts.size} modelos · máximo 3 por modelo`;
    $('ce-save-deck').disabled = count !== 30 || !$('ce-deck-name').value.trim() || !$('ce-leader').value;
    renderInventory();
    renderSelected();
  }

  function renderDecks() {
    const container = $('ce-decks');
    if (!app.decks.length) {
      container.innerHTML = '<p class="ce-empty">Você ainda não salvou decks. Monte o primeiro acima.</p>';
      return;
    }
    container.innerHTML = app.decks.map((deck) => `
      <div class="ce-deck-row">
        <div><strong>${esc(deck.name)}</strong><small>30 cartas · versão ${deck.version} · líder ${esc(deck.leader_id || 'não definido')}</small><small>ID ${esc(deck.deck_id)}</small></div>
        <div class="ce-deck-actions"><button class="ce-button ce-ghost" data-edit-deck="${esc(deck.deck_id)}">Editar</button><button class="ce-button ce-danger" data-delete-deck="${esc(deck.deck_id)}">Excluir</button></div>
      </div>`).join('');
    container.querySelectorAll('[data-edit-deck]').forEach((button) => button.addEventListener('click', () => editDeck(button.dataset.editDeck)));
    container.querySelectorAll('[data-delete-deck]').forEach((button) => button.addEventListener('click', () => deleteDeck(button.dataset.deleteDeck)));
  }

  function renderMatches() {
    const container = $('ce-matches');
    if (!app.matches.length) {
      container.innerHTML = '<p class="ce-empty">Nenhuma partida encontrada. Crie um desafio no Discord e ela aparecerá aqui.</p>';
      return;
    }
    container.innerHTML = app.matches.map((match) => `
      <div class="ce-match-row"><div><strong>Partida #${match.match_id}</strong><small>${match.status === 'active' ? 'Em andamento' : 'Encerrada'} · adversário ...${String(match.opponent_player_id || '').slice(-4)}</small><small>Revisão ${match.state_revision}</small></div><button class="ce-button ce-primary" data-open-match="${match.match_id}">Abrir</button></div>`).join('');
    container.querySelectorAll('[data-open-match]').forEach((button) => button.addEventListener('click', () => openMatch(Number(button.dataset.openMatch))));
  }

  async function refreshBootstrap() {
    clearNotify();
    $('ce-status-title').textContent = 'Atualizando dados';
    $('ce-status-text').textContent = 'Consultando coleção, decks e partidas.';
    const data = await api('/api/card-engine-v2/bootstrap');
    app.data = data;
    app.inventory = new Map(data.inventory.map((item) => [Number(item.exemplar_id), item]));
    app.cards = new Map(data.cards.map((item) => [item.card_id, item]));
    app.decks = data.decks || [];
    app.matches = data.matches || [];
    $('ce-collection-count').textContent = data.inventory.length;
    renderLeaders();
    renderBuilder();
    renderDecks();
    renderMatches();
    $('ce-status-title').textContent = 'Card Engine v2 conectado';
    $('ce-status-text').textContent = `${data.cards.length} modelos liberados · ${data.decks.length} decks salvos · dados privados autenticados.`;
  }

  async function editDeck(deckId) {
    const deck = app.decks.find((item) => item.deck_id === deckId);
    if (!deck) return;
    const missing = (deck.exemplar_ids || []).filter((id) => !app.inventory.has(Number(id)));
    if (missing.length) return notify(`Este deck contém ${missing.length} exemplar(es) que não estão mais na sua coleção. Ele não pode ser editado até ser reconstruído.`);
    app.editor = { deckId: deck.deck_id, version: deck.version, selected: deck.exemplar_ids.map(Number), name: deck.name, leaderId: deck.leader_id };
    $('ce-deck-name').value = deck.name;
    $('ce-leader').value = deck.leader_id;
    $('ce-cancel-edit').hidden = false;
    $('ce-save-deck').textContent = 'Atualizar deck';
    renderBuilder();
    document.querySelector('.ce-main-column .ce-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  async function saveDeck() {
    const name = $('ce-deck-name').value.trim();
    const leaderId = $('ce-leader').value;
    const cardIds = app.editor.selected.map((id) => app.inventory.get(Number(id))?.card_id);
    if (!name || !leaderId || app.editor.selected.length !== 30 || cardIds.some((id) => !id)) return notify('Preencha nome, líder e 30 exemplares válidos.');
    const button = $('ce-save-deck');
    button.disabled = true;
    try {
      const body = { name, card_ids: cardIds, exemplar_ids: app.editor.selected, leader_id: leaderId };
      if (app.editor.deckId) {
        await api(`/api/card-engine-v2/decks/${encodeURIComponent(app.editor.deckId)}`, {
          method: 'PUT', body: { ...body, expected_version: app.editor.version }
        });
        notify('Deck atualizado. A versão foi incrementada e a propriedade dos 30 exemplares foi revalidada.', true);
      } else {
        await api('/api/card-engine-v2/decks', { method: 'POST', body });
        notify('Deck salvo. Os exemplares continuam pertencendo à sua coleção.', true);
      }
      resetEditor();
      await refreshBootstrap();
    } catch (error) {
      notify(error.message);
      if (error.status === 409) await refreshBootstrap();
    } finally { button.disabled = false; }
  }

  async function deleteDeck(deckId) {
    const deck = app.decks.find((item) => item.deck_id === deckId);
    if (!deck || !window.confirm(`Excluir o deck “${deck.name}”? Nenhuma carta será removida da coleção.`)) return;
    try {
      await api(`/api/card-engine-v2/decks/${encodeURIComponent(deckId)}`, { method: 'DELETE', body: { expected_version: deck.version } });
      notify('Deck excluído. Sua coleção permaneceu intacta.', true);
      if (app.editor.deckId === deckId) resetEditor();
      await refreshBootstrap();
    } catch (error) { notify(error.message); }
  }

  function stopPolling() {
    if (app.pollTimer) window.clearInterval(app.pollTimer);
    app.pollTimer = null;
  }

  async function matchRequest(matchId, after = 0) {
    return api(`/api/card-engine-v2/matches/${matchId}?after=${after}`);
  }

  async function openMatch(matchId) {
    stopPolling();
    try {
      const data = await matchRequest(matchId, 0);
      app.activeMatch = {
        id: matchId,
        view: data.view,
        history: data.history.events || [],
        cursor: data.history.next_cursor || 0,
        hasMore: Boolean(data.history.has_more),
      };
      renderMatch();
      $('ce-match-panel').hidden = false;
      $('ce-match-panel').scrollIntoView({ behavior: 'smooth', block: 'start' });
      app.pollTimer = window.setInterval(() => refreshActiveMatch().catch(() => {}), 10000);
    } catch (error) { notify(error.message); }
  }

  function playerNames(state) {
    const ids = Object.keys(state.players || {});
    const ownId = String(app.data.player_id);
    const opponentId = ids.find((id) => id !== ownId) || 'oponente';
    return { ownId, opponentId, own: state.players[ownId], opponent: state.players[opponentId] };
  }

  function boardHTML(player, label) {
    const rows = { melee: 'Corpo a corpo', ranged: 'Longa distância', siege: 'Cerco' };
    const board = player?.board || [];
    return `<div class="ce-board"><h3>${esc(label)} · ${player?.life ?? 0} vida · ${player?.score ?? 0} poder</h3>${Object.entries(rows).map(([key, name]) => {
      const units = board.filter((unit) => unit.row === key);
      return `<div class="ce-row"><span>${name}</span><strong>${units.length ? units.map((unit) => `${esc(unit.name)} (${unit.effective_power})`).join(' · ') : '—'}</strong></div>`;
    }).join('')}</div>`;
  }

  function renderMatch() {
    if (!app.activeMatch) return;
    const state = app.activeMatch.view;
    const { ownId, opponentId, own, opponent } = playerNames(state);
    if (!own) return notify('A projeção autenticada desta partida não está disponível.');
    $('ce-match-title').textContent = `Partida #${app.activeMatch.id} · Rodada ${state.round_number ?? '—'}`;
    const current = String(state.current_player_id || '');
    const isOwnTurn = state.status === 'active' && current === ownId;
    $('ce-match-status').textContent = state.status === 'finished' ? 'Encerrada' : (isOwnTurn ? 'Sua vez' : 'Vez do adversário');
    $('ce-match-overview').innerHTML = [
      ['Sua vida', own.life ?? 0], ['Energia', `${own.energy ?? 0}/${own.maximum_energy ?? 5}`],
      ['Cartas na mão', own.hand_count ?? (own.hand || []).length], ['Deck / fatigue', `${own.draw_pile_count ?? 0} / ${own.deck_fatigue_count ?? 0}`]
    ].map(([label, value]) => `<div class="ce-stat"><strong>${esc(value)}</strong><small>${esc(label)}</small></div>`).join('');
    $('ce-match-boards').innerHTML = boardHTML(own, 'Você') + boardHTML(opponent, 'Adversário');
    $('ce-pass-turn').disabled = !isOwnTurn || state.status !== 'active';
    $('ce-activate-leader').disabled = !isOwnTurn || state.status !== 'active' || own.leader_used || !own.leader_id;
    $('ce-sacrifice').disabled = !isOwnTurn || state.status !== 'active' || !(own.board || []).length;
    const hand = own.hand || [];
    $('ce-match-hand').innerHTML = hand.length ? hand.map((card) => {
      const meta = app.cards.get(card.card_id) || {};
      return `<div class="ce-card-row"><div class="ce-card-info"><strong>${esc(card.name || meta.name || card.card_id)}</strong><small>${esc(meta.kind || 'carta')} · ${card.energy_cost ?? meta.energy_cost ?? '—'} energia · ${card.instance_id ? 'instância pronta' : ''}</small></div><button class="ce-button ce-primary" data-play-card="${esc(card.instance_id)}" ${!isOwnTurn ? 'disabled' : ''}>Jogar</button></div>`;
    }).join('') : '<p class="ce-empty">Sua mão está vazia.</p>';
    $('ce-match-hand').querySelectorAll('[data-play-card]').forEach((button) => button.addEventListener('click', () => playCard(button.dataset.playCard)));
    $('ce-history').innerHTML = app.activeMatch.history.length ? app.activeMatch.history.map((event) => {
      const actor = event.subject === 'you' ? 'Você' : event.subject === 'opponent' ? 'Adversário' : 'Sistema';
      const label = String(event.kind || 'evento').replaceAll('_', ' ');
      const payload = event.payload || {};
      const info = [payload.row && `fileira ${payload.row}`, payload.damage != null && `dano ${payload.damage}`, payload.energy_spent != null && `energia ${payload.energy_spent}`, event.target_count && `${event.target_count} alvo(s)`].filter(Boolean).join(' · ');
      return `<div class="ce-event"><small>#${event.sequence}</small> <strong>${esc(actor)}</strong> · ${esc(label)}${info ? `<br>${esc(info)}` : ''}</div>`;
    }).join('') : '<p class="ce-empty">Ainda não há eventos.</p>';
    $('ce-history-more').hidden = !app.activeMatch.hasMore;
    $('ce-match-poll').textContent = `Atualização automática · revisão ${state.state_revision} · 10 s`;
  }

  async function refreshActiveMatch() {
    if (!app.activeMatch) return;
    const cursor = app.activeMatch.cursor;
    const data = await matchRequest(app.activeMatch.id, cursor);
    const oldRevision = Number(app.activeMatch.view.state_revision || 0);
    app.activeMatch.view = data.view;
    const newEvents = data.history.events || [];
    if (newEvents.length) {
      app.activeMatch.history.push(...newEvents);
      app.activeMatch.cursor = data.history.next_cursor || cursor;
    }
    app.activeMatch.hasMore = Boolean(data.history.has_more);
    if (Number(data.view.state_revision || 0) !== oldRevision || newEvents.length) renderMatch();
    if (data.view.status === 'finished') stopPolling();
  }

  async function performAction(action, payload) {
    if (!app.activeMatch) return;
    try {
      const result = await api(`/api/card-engine-v2/matches/${app.activeMatch.id}/actions`, {
        method: 'POST',
        body: { action, payload: { ...payload, expected_revision: app.activeMatch.view.state_revision, operation_id: crypto.randomUUID() } },
      });
      app.activeMatch.view = result.view;
      await refreshActiveMatch();
      notify(result.result?.outcome === 'rejected' ? 'Ação recusada pelas regras da partida.' : 'Ação processada.', result.result?.outcome !== 'rejected');
    } catch (error) {
      notify(error.message);
      if (error.status === 409) await refreshActiveMatch();
    }
  }

  async function playCard(instanceId) {
    const { ownId, own } = playerNames(app.activeMatch.view);
    const card = (own.hand || []).find((item) => item.instance_id === instanceId);
    if (!card) return notify('A carta não está mais na sua mão. Atualize a partida.');
    const meta = app.cards.get(card.card_id) || {};
    if (meta.kind === 'unit') return performAction('play_unit', { instance_id: instanceId });
    if (meta.kind !== 'special') return notify('Este tipo de carta ainda não possui ação na interface web.');
    const needsRow = ['gwent_clima', 'gwent_geada_cariana', 'gwent_execucao'].includes(meta.effect_id);
    const needsTarget = ['gwent_egide', 'gwent_execucao'].includes(meta.effect_id);
    if (!needsRow && !needsTarget) return performAction('play_special', { source_instance_id: instanceId, selection: {} });
    choose(['melee', 'ranged', 'siege'].map((row) => ({ label: ({ melee: 'Corpo a corpo', ranged: 'Longa distância', siege: 'Cerco' })[row], value: row })), 'Escolha a fileira', async (row) => {
      if (needsTarget) {
        const offer = await api(`/api/card-engine-v2/matches/${app.activeMatch.id}/target-offer`, { method: 'POST', body: { source_instance_id: instanceId, selected_row: row } });
        choose((offer.candidates || []).map((candidate) => ({ label: candidate.display_name || candidate.display_metric_value || 'Alvo', value: candidate.target_instance_id })), 'Escolha o alvo', (target) => performAction('play_special', { source_instance_id: instanceId, selected_row: row, selection: { mode: 'manual_single', target_instance_id: target } }));
      } else performAction('play_special', { source_instance_id: instanceId, selected_row: row, selection: {} });
    });
  }

  function choose(options, title, callback) {
    const modal = $('ce-modal');
    $('ce-modal-content').innerHTML = `<p class="eyebrow">AÇÃO DA PARTIDA</p><h2>${esc(title)}</h2><div class="ce-choice-list">${options.map((item, index) => `<button class="ce-button ce-ghost" data-choice="${index}">${esc(item.label)}</button>`).join('')}</div>`;
    $('ce-modal-content').querySelectorAll('[data-choice]').forEach((button) => button.addEventListener('click', async () => {
      const selected = options[Number(button.dataset.choice)];
      modal.hidden = true;
      try { await callback(selected.value); } catch (error) { notify(error.message); }
    }));
    if (!options.length) $('ce-modal-content').innerHTML += '<p class="ce-empty">Nenhuma opção válida disponível.</p>';
    modal.hidden = false;
  }

  async function loadMoreHistory() {
    if (!app.activeMatch || !app.activeMatch.hasMore) return;
    try {
      const data = await matchRequest(app.activeMatch.id, app.activeMatch.cursor);
      app.activeMatch.history.push(...(data.history.events || []));
      app.activeMatch.cursor = data.history.next_cursor || app.activeMatch.cursor;
      app.activeMatch.hasMore = Boolean(data.history.has_more);
      renderMatch();
    } catch (error) { notify(error.message); }
  }

  $('ce-card-filter').addEventListener('input', renderInventory);
  $('ce-deck-name').addEventListener('input', renderBuilder);
  $('ce-leader').addEventListener('change', renderBuilder);
  $('ce-save-deck').addEventListener('click', saveDeck);
  $('ce-cancel-edit').addEventListener('click', resetEditor);
  $('ce-refresh').addEventListener('click', () => refreshBootstrap().catch((error) => notify(error.message)));
  $('ce-refresh-matches').addEventListener('click', () => refreshBootstrap().catch((error) => notify(error.message)));
  $('ce-pass-turn').addEventListener('click', () => performAction('pass_turn', {}));
  $('ce-activate-leader').addEventListener('click', () => choose(
    [{ label: 'Corpo a corpo', value: 'melee' }, { label: 'Longa distância', value: 'ranged' }, { label: 'Cerco', value: 'siege' }],
    'Escolha a fileira para o líder', (row) => performAction('activate_leader', { selected_row: row })
  ));
  $('ce-sacrifice').addEventListener('click', async () => {
    try {
      const offer = await api(`/api/card-engine-v2/matches/${app.activeMatch.id}/sacrifice-offer`, { method: 'POST', body: {} });
      choose((offer.candidates || []).map((item) => ({ label: `${item.display_name || 'Unidade'} · poder ${item.display_metric_value ?? '—'}`, value: item.target_instance_id })), 'Escolha a unidade que será sacrificada', (target) => performAction('sacrifice_unit', { target_instance_id: target }));
    } catch (error) { notify(error.message); }
  });
  $('ce-history-more').addEventListener('click', loadMoreHistory);
  $('ce-close-match').addEventListener('click', () => { stopPolling(); app.activeMatch = null; $('ce-match-panel').hidden = true; });
  $('ce-modal-close').addEventListener('click', () => { $('ce-modal').hidden = true; });
  $('ce-modal').addEventListener('click', (event) => { if (event.target === $('ce-modal')) $('ce-modal').hidden = true; });

  refreshBootstrap().catch((error) => {
    $('ce-status-title').textContent = 'Não foi possível conectar';
    $('ce-status-text').textContent = 'Verifique sua sessão do site e tente novamente.';
    notify(error.message);
  });
})();
