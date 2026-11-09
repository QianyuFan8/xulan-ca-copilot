// XULAN Advisor Studio — vanilla JS front end for the FastAPI service.
// All model text is rendered with textContent (never innerHTML).
const $ = (id) => document.getElementById(id);
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const SCENARIO_LABELS = {
  greeting: 'Greeting',
  recommendation: 'Recommend',
  care: 'Care',
  reactivation: 'Reconnect',
  invitation: 'Invite',
  price_objection: 'Price concern',
};
const OCCASIONS = ['生日', '春节', '中秋节', '元旦', '七夕', '圣诞节'];
const CONTACT_LABELS = { allowed: 'Contact permitted', no_marketing: 'No marketing', no_contact: 'No proactive contact' };

const state = {
  config: { scenarios: {}, products: [] },
  clients: [],
  events: [],
  examples: [],
  thread: [],             // [{role: 'client' | 'advisor', content}]
  role: 'client',          // role for the next added message
  scenario: 'greeting',
  fields: {},              // scenario field values, kept across scenario switches
  contact: {},             // per-client contact preference overrides
  newClient: {             // editable record for a client who is not in the list
    id: 'NEW',
    preferred_address: '',
    preferences: '',
    relationship_stage: 'New contact',
    contact_preference: 'allowed',
    timezone: 'Asia/Shanghai',
  },
  result: null,
  edited: null,            // the CA's edited wording of each draft
  selected: 0,
  busy: false,
  inputVersion: 0,         // bumped on every input edit; a reply for an older version is discarded
  sessions: {},            // per client, for this page: the conversation and last-contact time
  activeClient: null,
};

// ---------- helpers ----------
const pad = (n) => String(n).padStart(2, '0');
const localInput = (date) =>
  `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
const toIso = (value) => (value ? new Date(value).toISOString() : null);
const price = (p) => `¥${(p.price_minor / 100).toLocaleString()}`;
const productById = (sku) => state.config.products.find((p) => p.sku === sku);
const eventById = (id) => state.events.find((e) => e.id === id);
const NEW_CLIENT = '__new__';
const STAGES = ['New contact', 'Established contact', 'Returning client'];
const TIMEZONES = ['Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Singapore', 'Asia/Tokyo', 'Europe/London', 'Europe/Paris', 'America/New_York'];
const currentClient = () =>
  $('client').value === NEW_CLIENT ? state.newClient : state.clients.find((c) => c.id === $('client').value);
const fmtTime = (iso) => iso.slice(11, 16);
const fmtDate = (iso) => {
  const [, m, d] = iso.slice(0, 10).split('-');
  return `${Number(m)}月${Number(d)}日`;
};

function notice(text) {
  $('status').textContent = text || '';
}

function showFormError(text) {
  $('form-error').textContent = text || '';
  $('form-error').hidden = !text;
}

// Any edit after a result means the drafts no longer match the inputs.
function markStale() {
  state.inputVersion += 1;
  showFormError('');
  if (state.result && !state.busy) notice('Inputs changed. These drafts belong to the previous input; regenerate before use.');
}

// ---------- client ----------
// Editable card for a new client: every field the request uses can be typed in.
function renderNewClientCard(card) {
  const c = state.newClient;
  const update = (key, value) => {
    c[key] = value;
    if (key === 'preferred_address') $('recipient').textContent = value || 'New client';
    markStale();
  };
  const input = (id, key, placeholder) => {
    const i = el('input');
    i.id = id;
    i.value = c[key];
    i.placeholder = placeholder;
    i.maxLength = key === 'preferred_address' ? 80 : 2000;
    i.oninput = () => update(key, i.value);
    return i;
  };
  const select = (id, key, options) => {
    const s = el('select');
    s.id = id;
    for (const [value, label] of options) {
      const o = el('option', null, label);
      o.value = value;
      s.append(o);
    }
    s.value = c[key] ?? '';
    s.onchange = () => update(key, s.value);
    return s;
  };
  const prefs = el('textarea');
  prefs.id = 'new-preferences';
  prefs.rows = 2;
  prefs.maxLength = 2000;
  prefs.placeholder = '喜欢深色、低调的款式，日常通勤用';
  prefs.value = c.preferences;
  prefs.oninput = () => update('preferences', prefs.value);

  const top = el('div', 'pair');
  top.append(
    field('Preferred address', input('new-address', 'preferred_address', '赵女士'), 'Required'),
    field('Relationship', select('new-stage', 'relationship_stage', STAGES.map((s) => [s, s]))),
  );
  const bottom = el('div', 'pair');
  bottom.append(
    field('Timezone', select('new-timezone', 'timezone', [...TIMEZONES.map((z) => [z, z]), ['', 'Unknown']])),
    field('Contact preference', select('new-contact', 'contact_preference', Object.entries(CONTACT_LABELS))),
  );
  card.append(el('p', 'client-new-title', 'New client · enter what you know'), top, field('Preferences and notes', prefs, 'Only what the client has told you'), bottom);
  $('recipient').textContent = c.preferred_address || 'New client';
}

function renderClientCard() {
  const c = currentClient();
  const card = $('client-card');
  card.replaceChildren();
  card.classList.toggle('editable', $('client').value === NEW_CLIENT);
  if (!c) return;
  if ($('client').value === NEW_CLIENT) {
    renderNewClientCard(card);
    return;
  }
  const head = el('div', 'client-head');
  head.append(el('span', 'client-name', c.preferred_address), el('span', 'client-id', `${c.id} · ${c.relationship_stage}`));
  const prefs = el('p', 'client-prefs', c.preferences || 'No recorded preferences');
  const meta = el('div', 'client-meta');
  meta.append(el('span', null, `Timezone ${c.timezone || 'unknown'}`));

  const contactWrap = el('label', 'contact-select');
  contactWrap.append(el('span', null, 'Contact preference'));
  const select = el('select');
  select.id = 'contact';
  for (const [value, label] of Object.entries(CONTACT_LABELS)) {
    const o = el('option', null, label);
    o.value = value;
    select.append(o);
  }
  select.value = state.contact[c.id] || c.contact_preference || 'allowed';
  select.onchange = () => {
    state.contact[c.id] = select.value;
    markStale();
  };
  contactWrap.append(select);
  card.append(head, prefs, meta, contactWrap);
  $('recipient').textContent = c.preferred_address;
}

// ---------- conversation thread ----------
function renderThread() {
  const box = $('thread');
  box.replaceChildren();
  if (!state.thread.length) {
    box.append(el('p', 'thread-empty', 'No messages yet. Add the client\'s latest message below.'));
  }
  state.thread.forEach((m, i) => {
    // Client messages on the left, the advisor's own messages on the right, as in WeChat.
    const row = el('div', `msg ${m.role}`);
    const meta = el('div', 'msg-meta');
    const remove = el('button', 'msg-remove', 'Remove');
    remove.type = 'button';
    remove.setAttribute('aria-label', `Remove ${m.role} message ${i + 1}`);
    remove.onclick = () => {
      state.thread.splice(i, 1);
      renderThread();
      markStale();
    };
    const when = m.timestamp ? ` · ${new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : '';
    meta.append(el('span', 'msg-role', (m.role === 'client' ? 'Client' : 'You') + when), remove);
    row.append(meta, el('div', 'msg-bubble', m.content));
    box.append(row);
  });
  requestAnimationFrame(() => (box.scrollTop = box.scrollHeight)); // newest message in view, after layout
  renderSuggestion();
  renderPhone();
}

// The client's recent conversation from the CRM record (synthetic here).
// Keep what the CA did for one client (messages added, drafts marked as sent, last contact) while they
// look at another client, and restore it on return. Page memory only: the CRM stays the source of truth.
function saveSession() {
  if (state.activeClient) state.sessions[state.activeClient] = { thread: state.thread, lastContact: $('last-contact').value };
}

function openSession(id) {
  const saved = state.sessions[id];
  state.thread = saved ? saved.thread : clientHistory(currentClient());
  $('last-contact').value = saved ? saved.lastContact : '';
  state.activeClient = id;
}

function clientHistory(client) {
  return (client?.recent_conversation || []).map((h) => ({ role: h.role, content: h.content }));
}

function setRole(role) {
  state.role = role;
  for (const b of document.querySelectorAll('.role-toggle button')) b.setAttribute('aria-checked', String(b.dataset.role === role));
  $('new-message').placeholder = role === 'client' ? "Paste the client's latest message" : 'Add something you already sent';
}

function addMessage() {
  const text = $('new-message').value.trim();
  if (!text) {
    showFormError('Type a message before adding it.');
    $('new-message').focus();
    return;
  }
  showFormError('');
  state.thread.push({ role: state.role, content: text, timestamp: new Date().toISOString() });
  $('new-message').value = '';
  renderThread();
  markStale();
}

// ---------- scenario ----------
function renderScenarios() {
  const box = $('scenarios');
  box.replaceChildren();
  for (const key of Object.keys(state.config.scenarios)) {
    const b = el('button', 'scenario', SCENARIO_LABELS[key] || key);
    b.type = 'button';
    b.setAttribute('role', 'radio');
    b.setAttribute('aria-checked', String(key === state.scenario));
    b.title = state.config.scenarios[key];
    b.onclick = () => setScenario(key);
    box.append(b);
  }
}

function setScenario(key) {
  state.scenario = key;
  renderScenarios();
  renderFields();
  renderSuggestion();
  markStale();
}

// Rule-based suggestion from the latest client message. The CA always decides.
function suggestScenario() {
  const last = [...state.thread].reverse().find((m) => m.role === 'client');
  if (!last) return null;
  const t = last.content;
  if (/折扣|打折|优惠|便宜|太贵|贵了|预算|赠品|优惠券|差价/.test(t)) return 'price_objection';
  if (/划痕|保养|护理|淋|雨|清洁|掉色|污渍|磨损|存放|维修/.test(t)) return 'care';
  if (/活动|预览|展览|展示|沙龙/.test(t)) return 'invitation';
  if (/推荐|想找|有没有|适合|通勤|款式/.test(t)) return 'recommendation';
  return null;
}

function renderSuggestion() {
  const box = $('suggestion');
  const s = suggestScenario();
  box.replaceChildren();
  if (!s || s === state.scenario) {
    box.hidden = true;
    return;
  }
  const use = el('button', 'link', `Use ${SCENARIO_LABELS[s]}`);
  use.type = 'button';
  use.onclick = () => setScenario(s);
  box.append(el('span', null, `The latest client message looks like “${SCENARIO_LABELS[s]}”.`), use);
  box.hidden = false;
}

// ---------- scenario-specific fields (no raw JSON) ----------
function field(labelText, control, hint) {
  const wrap = el('div', 'field');
  const label = el('label', null, labelText);
  label.htmlFor = control.id;
  if (hint) label.append(el('span', 'hint', hint));
  wrap.append(label, control);
  return wrap;
}

function productSelect(optional) {
  const select = el('select');
  select.id = 'product';
  const none = el('option', null, optional ? 'No product (optional)' : 'Select a product');
  none.value = '';
  select.append(none);
  for (const p of state.config.products) {
    const o = el('option', null, `${p.name} · ${price(p)}`);
    o.value = p.sku;
    select.append(o);
  }
  select.value = state.fields.product || '';
  const facts = el('p', 'facts');
  const showFacts = () => {
    const p = productById(select.value);
    facts.textContent = p ? `${p.material} · ${p.dimensions_cm} cm · ${price(p)} · ${p.design}` : '';
  };
  select.onchange = () => {
    state.fields.product = select.value;
    showFacts();
    markStale();
  };
  showFacts();
  const wrap = field('Product', select, optional ? 'Optional' : 'Verified catalogue facts only');
  wrap.append(facts);
  return wrap;
}

function renderFields() {
  const box = $('fields');
  box.replaceChildren();
  const s = state.scenario;
  const bind = (control, key) => {
    control.value = state.fields[key] ?? '';
    control.oninput = () => {
      state.fields[key] = control.value;
      markStale();
    };
    return control;
  };

  if (s === 'greeting') {
    const occasion = el('select');
    occasion.id = 'occasion';
    for (const o of OCCASIONS) occasion.append(el('option', null, o));
    if (!state.fields.occasion) state.fields.occasion = OCCASIONS[0];
    const date = el('input');
    date.type = 'date';
    date.id = 'occasion-date';
    const pair = el('div', 'pair');
    pair.append(field('Occasion', bind(occasion, 'occasion')), field('Date', bind(date, 'occasion_date')));
    box.append(pair);
  }
  if (['recommendation', 'care', 'price_objection'].includes(s)) box.append(productSelect(false));
  if (s === 'reactivation') box.append(productSelect(true));
  if (s === 'recommendation') {
    const budget = el('input');
    budget.type = 'number';
    budget.min = '0';
    budget.step = '100';
    budget.id = 'budget';
    budget.placeholder = '8000';
    const device = el('input');
    device.id = 'device';
    device.placeholder = '13-inch laptop';
    const pair = el('div', 'pair');
    pair.append(field('Hard budget (CNY)', bind(budget, 'budget'), 'Optional'), field('Must fit a device', bind(device, 'device'), 'Optional'));
    box.append(pair);
  }
  if (s === 'invitation') {
    const select = el('select');
    select.id = 'event';
    const none = el('option', null, 'Select an event');
    none.value = '';
    select.append(none);
    for (const e of state.events) {
      const o = el('option', null, `${e.title} · ${fmtDate(e.start)}`);
      o.value = e.id;
      select.append(o);
    }
    select.value = state.fields.event || '';
    const facts = el('dl', 'event-facts');
    const showFacts = () => {
      facts.replaceChildren();
      const e = eventById(select.value);
      if (!e) return;
      for (const [k, v] of [
        ['When', `${fmtDate(e.start)} ${fmtTime(e.start)}–${fmtTime(e.end)}`],
        ['Where', e.location],
        ['What', e.content],
        ['Booking', e.booking_route],
      ]) facts.append(el('dt', null, k), el('dd', null, v));
    };
    select.onchange = () => {
      state.fields.event = select.value;
      showFacts();
      markStale();
    };
    showFacts();
    const wrap = field('Event', select, 'Approved event facts, shown read-only');
    wrap.append(facts);
    box.append(wrap);
  }
}

function scenarioDetails() {
  const s = state.scenario;
  const f = state.fields;
  if (s === 'greeting') return { occasion: f.occasion || OCCASIONS[0], occasion_date: f.occasion_date || '' };
  if (s === 'invitation') {
    const e = eventById(f.event);
    if (!e) return {};
    const { id, ...facts } = e;
    return facts;
  }
  if (s === 'recommendation') {
    const d = {};
    if (f.budget) d.hard_budget_cny = Number(f.budget);
    if (f.device) d.required_device_fit = f.device;
    return d;
  }
  return {};
}

// Selections the form itself can check before calling the service.
function missingSelection() {
  const s = state.scenario;
  const f = state.fields;
  if (s === 'greeting' && !f.occasion_date) return 'Choose the occasion date.';
  if (['recommendation', 'care', 'price_objection'].includes(s) && !f.product) return 'Choose the product this message is about.';
  if (s === 'invitation' && !f.event) return 'Choose the event to invite the client to.';
  if ($('client').value === NEW_CLIENT && !state.newClient.preferred_address.trim()) return 'Enter how to address the new client.';
  return null;
}

function buildRequest() {
  const c = currentClient();
  return {
    scenario: state.scenario,
    client_information: {
      id: c.id,
      preferred_address: c.preferred_address,
      preferences: c.preferences,
      relationship_stage: c.relationship_stage,
      contact_preference: (c === state.newClient ? c.contact_preference : state.contact[c.id] || c.contact_preference) || 'allowed',
      timezone: c.timezone || null,
      last_outbound_contact: toIso($('last-contact').value),
    },
    conversation_history: state.thread,
    product_information: ['recommendation', 'care', 'price_objection', 'reactivation'].includes(state.scenario) && state.fields.product
      ? [state.fields.product]
      : [],
    scenario_details: scenarioDetails(),
    current_datetime: toIso($('reference').value) || new Date().toISOString(),
  };
}

// ---------- results ----------
const BANNERS = {
  needs_information: ['warn', 'A few details are needed before drafting', 'information_requests'],
  blocked: ['danger', 'This outreach is blocked by the client\'s contact preference', 'blocking_reasons'],
  error: ['danger', 'No drafts were produced', 'validation_findings'],
};

function banner(kind, title, items, extra) {
  const box = el('div', `banner ${kind}`);
  box.append(el('strong', null, title));
  if (items.length) {
    const ul = el('ul');
    for (const t of items) ul.append(el('li', null, t));
    box.append(ul);
  }
  if (extra) box.append(el('p', 'banner-extra', extra));
  return box;
}

function renderResult() {
  const data = state.result;
  const banners = $('banners');
  const options = $('options');
  banners.replaceChildren();
  options.replaceChildren();
  $('run').textContent = '';
  if (!data) {
    options.append($('empty-template').content.cloneNode(true));
    renderPhone();
    return;
  }
  if (BANNERS[data.status]) {
    const [kind, title, key] = BANNERS[data.status];
    const extra = data.status === 'error' ? `Run ${data.metadata.run_id}. Your inputs are kept; adjust them or try again.` : null;
    banners.append(banner(kind, title, data[key] || [], extra));
  }
  if (data.advisories?.length) banners.append(banner('warn', 'Before you send', data.advisories));

  if (data.status === 'success') {
    if (!state.edited || state.edited.length !== data.candidates.length) state.edited = [...data.candidates];
    data.candidates.forEach((_, i) => {
      const text = state.edited[i];
      const card = el('div', 'option');
      card.tabIndex = 0;
      card.setAttribute('role', 'radio');
      card.setAttribute('aria-checked', String(i === state.selected));
      const head = el('div', 'option-head');
      const count = el('span', 'count', `${[...text].length} chars`);
      head.append(el('span', null, `OPTION 0${i + 1}`), count);
      const copy = el('button', 'copy', 'Copy');
      copy.type = 'button';
      copy.onclick = async (event) => {
        event.stopPropagation();
        try {
          await navigator.clipboard.writeText(state.edited[i]);
          copy.textContent = 'Copied';
          setTimeout(() => (copy.textContent = 'Copy'), 1800);
        } catch {
          notice('Copy is unavailable here. Select the text and copy it manually.');
          const range = document.createRange();
          range.selectNodeContents(body);
          getSelection().removeAllRanges();
          getSelection().addRange(range);
        }
      };
      head.append(copy);
      const body = el('p', 'option-text', text);
      // Edit in place: the CA's wording is what gets copied, previewed and recorded as sent.
      const editor = el('textarea', 'option-edit');
      editor.rows = 4;
      editor.value = text;
      editor.hidden = true;
      editor.setAttribute('aria-label', `Edit option ${i + 1}`);
      editor.oninput = () => {
        state.edited[i] = editor.value;
        body.textContent = editor.value;
        count.textContent = `${[...editor.value].length} chars${editor.value !== data.candidates[i] ? ' · edited' : ''}`;
        if (state.selected === i) renderPhone();
      };
      const actions = el('div', 'option-actions');
      const edit = el('button', 'link', 'Edit');
      edit.type = 'button';
      edit.onclick = (event) => {
        event.stopPropagation();
        const editing = editor.hidden;
        editor.hidden = !editing;
        body.hidden = editing;
        edit.textContent = editing ? 'Done' : 'Edit';
        if (editing) editor.focus();
      };
      const sent = el('button', 'secondary small', 'Mark as sent');
      sent.type = 'button';
      sent.onclick = (event) => {
        event.stopPropagation();
        markAsSent(i);
      };
      actions.append(edit, sent);
      card.append(head, body, editor, actions);
      const choose = () => {
        state.selected = i;
        for (const o of options.querySelectorAll('.option')) o.setAttribute('aria-checked', 'false');
        card.setAttribute('aria-checked', 'true');
        renderPhone();
      };
      card.onclick = choose;
      card.onkeydown = (e) => {
        if (e.target !== card) return; // typing in the editor or using a button
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          choose();
        }
      };
      options.append(card);
    });
  } else {
    options.append($('empty-template').content.cloneNode(true));
  }
  const m = data.metadata || {};
  const parts = [`Run ${m.run_id}`];
  if (m.returned_model) parts.push(m.returned_model);
  parts.push(`prompt ${m.prompt_version}`, `${m.latency_seconds}s`);
  $('run').textContent = parts.join(' · ');
  renderPhone();
}

// The CA sent this draft (as edited): it becomes part of the conversation history for the next request.
function markAsSent(i) {
  const text = (state.edited?.[i] ?? state.result.candidates[i]).trim();
  if (!text) return;
  const sentAt = new Date();
  state.thread.push({ role: 'advisor', content: text, timestamp: sentAt.toISOString() });
  // Sending is advisor contact: record it so the seven-day recency advisory applies to the next draft.
  $('last-contact').value = localInput(sentAt);
  state.inputVersion += 1; // the history changed: any reply still in flight is for the old history
  state.result = null;
  state.edited = null;
  renderThread();
  renderResult();
  notice(`Option 0${i + 1} recorded as sent. Paste the client's reply when it arrives, then generate again.`);
}

// Phone preview: recent conversation plus the selected draft as an unsent outgoing bubble.
function renderPhone() {
  const chat = $('chat');
  chat.replaceChildren();
  for (const m of state.thread.slice(-3)) chat.append(el('div', `chat-msg ${m.role === 'client' ? 'in' : 'out sent'}`, m.content));
  const data = state.result;
  if (data?.status === 'success') {
    const draft = el('div', 'chat-msg out draft', state.edited?.[state.selected] ?? data.candidates[state.selected]);
    chat.append(el('p', 'chat-caption', `OPTION 0${state.selected + 1} · NOT SENT`), draft);
  } else if (!state.thread.length) {
    chat.append(el('p', 'chat-placeholder', 'The selected draft will appear here, in context.'));
  }
}

// ---------- examples ----------
function loadExample() {
  const e = state.examples.find((x) => x.scenario === state.scenario);
  if (!e) return;
  const id = e.client_information.id;
  saveSession();
  if (state.clients.some((c) => c.id === id)) $('client').value = id;
  // Client's recent conversation first, then the example's newest message(s), without duplicates.
  const thread = clientHistory(currentClient());
  for (const h of e.conversation_history) {
    if (!thread.some((m) => m.role === h.role && m.content === h.content)) thread.push({ role: h.role, content: h.content });
  }
  state.thread = thread;
  state.activeClient = $('client').value;
  const d = e.scenario_details || {};
  state.fields = {
    ...state.fields,
    product: e.product_information[0] || '',
    occasion: d.occasion || state.fields.occasion,
    occasion_date: d.occasion_date || state.fields.occasion_date,
    event: state.events.find((x) => x.title === d.title)?.id || state.fields.event,
  };
  state.result = null;
  renderClientCard();
  renderThread();
  renderFields();
  renderResult();
  notice('Synthetic example loaded. Review the dates before generating.');
}

// ---------- generate ----------
async function generate(event) {
  event.preventDefault();
  if (state.busy) return;
  showFormError('');
  if (!currentClient()) {
    showFormError('Choose a client first.');
    return;
  }
  const missing = missingSelection();
  if (missing) {
    showFormError(missing);
    return;
  }
  const request = buildRequest();
  const sentFor = { version: state.inputVersion, client: $('client').value };
  // Previous drafts belong to the previous inputs: remove them now, so they cannot be copied or marked as
  // sent while this request runs or after it fails. The inputs themselves are kept.
  state.result = null;
  state.edited = null;
  renderResult();
  state.busy = true;
  $('generate').disabled = true;
  $('example').disabled = true;
  notice('Considering the context and drafting three options…');
  try {
    const response = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(response.status === 422 ? 'Some details are in an unexpected format. Check the dates and the budget.' : 'The service could not complete this request.');
    }
    if (sentFor.version !== state.inputVersion || sentFor.client !== $('client').value) {
      // The client or the inputs changed while drafting: these drafts no longer match what is on screen.
      notice('The client or inputs changed while drafting, so those drafts were discarded. Generate again.');
      return;
    }
    state.result = data;
    state.edited = data.candidates ? [...data.candidates] : null;
    state.selected = 0;
    renderResult();
    notice({
      success: 'Three drafts, ready for your review.',
      needs_information: '',
      blocked: '',
      error: '',
    }[data.status]);
  } catch (e) {
    notice(e.message || 'Connection failed. Your inputs are kept.');
  } finally {
    state.busy = false;
    $('generate').disabled = false;
    $('example').disabled = false;
    refreshHealth();
  }
}

async function refreshHealth() {
  try {
    const h = await (await fetch('/api/health')).json();
    $('health').textContent = `${h.credential_configured ? 'Model connected' : 'Model credential not configured'} · $${h.budget.estimated_or_reserved_usd.toFixed(2)} of $${h.budget.operating_limit_usd.toFixed(2)} used`;
  } catch {
    $('health').textContent = 'Local service unavailable';
  }
}

// ---------- init ----------
function bindEvents() {
  $('form').addEventListener('submit', generate);
  $('example').onclick = loadExample;
  $('add-message').onclick = addMessage;
  $('new-message').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addMessage();
    }
  });
  for (const b of document.querySelectorAll('.role-toggle button')) b.onclick = () => setRole(b.dataset.role);
  $('client').onchange = () => {
    // The conversation and last-contact time belong to the client: never carry them over, and restore
    // what was recorded for this client earlier on the page.
    saveSession();
    openSession($('client').value);
    // Drafts belong to the client they were written for: never carry them over to another client.
    state.result = null;
    state.edited = null;
    markStale();
    renderThread();
    renderClientCard();
    renderResult();
    if (!state.busy) notice('');
  };
  for (const id of ['reference', 'last-contact']) $(id).addEventListener('input', markStale);
}

(async function init() {
  // Keep the empty state as a reusable template.
  const tpl = document.createElement('template');
  tpl.id = 'empty-template';
  tpl.content.append($('empty').cloneNode(true));
  document.body.append(tpl);

  bindEvents();
  const now = new Date();
  $('reference').value = localInput(now);
  state.fields.occasion_date = localInput(now).slice(0, 10); // local date, not UTC
  try {
    const load = async (url) => (await fetch(url)).json();
    [state.config, state.clients, state.events, state.examples] = await Promise.all(
      ['/api/config', '/api/clients', '/api/events', '/api/examples'].map(load),
    );
    for (const c of state.clients) {
      const o = el('option', null, `${c.preferred_address} · ${c.id} · ${c.relationship_stage}`);
      o.value = c.id;
      $('client').append(o);
    }
    const fresh = el('option', null, '+ New client…');
    fresh.value = NEW_CLIENT;
    $('client').append(fresh);
    renderScenarios();
    loadExample();
    notice('');
    refreshHealth();
  } catch {
    notice('Could not load the studio configuration. Refresh once the service is running.');
  }
})();
