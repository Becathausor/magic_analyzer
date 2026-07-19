const decklistListEl = document.getElementById('decklist-list');
const deckViewEl = document.getElementById('deck-view');
const tooltipEl = document.getElementById('tooltip');

const ZONE_LABELS = {
  commander_zone: 'Commander',
  main_deck: 'Main Deck',
  sideboard_zone: 'Sideboard',
  considering_zone: 'Considering',
};
const ZONE_ORDER = ['commander_zone', 'main_deck', 'sideboard_zone', 'considering_zone'];

const cardCache = new Map();
let pollTimer = null;

async function loadDecklists() {
  const res = await fetch('/api/decklists');
  const filenames = await res.json();
  decklistListEl.innerHTML = '';
  for (const filename of filenames) {
    const li = document.createElement('li');
    li.textContent = filename;
    li.addEventListener('click', () => selectDecklist(filename, li));
    decklistListEl.appendChild(li);
  }
}

async function selectDecklist(filename, li) {
  for (const other of decklistListEl.children) {
    other.classList.remove('active');
  }
  li.classList.add('active');

  deckViewEl.innerHTML = '<p class="placeholder">Loading…</p>';
  const res = await fetch(`/api/decklists/${encodeURIComponent(filename)}`);
  if (!res.ok) {
    deckViewEl.innerHTML = '<p class="placeholder">Failed to load decklist.</p>';
    return;
  }
  const deck = await res.json();
  renderDeck(deck);
}

function renderDeck(deck) {
  deckViewEl.innerHTML = '';
  for (const zoneKey of ZONE_ORDER) {
    const rows = deck[zoneKey];
    if (!rows || rows.length === 0) continue;

    const section = document.createElement('section');
    section.className = 'zone';

    const heading = document.createElement('h2');
    heading.textContent = ZONE_LABELS[zoneKey];
    section.appendChild(heading);

    for (const { cardname, quantity } of rows) {
      const row = document.createElement('div');
      row.className = 'card-row';
      row.textContent = `${quantity} ${cardname}`;
      row.addEventListener('mouseenter', (event) => {
        positionTooltip(event);
        handleHoverStart(cardname);
      });
      row.addEventListener('mousemove', positionTooltip);
      row.addEventListener('mouseleave', handleHoverEnd);
      section.appendChild(row);
    }

    deckViewEl.appendChild(section);
  }
}

function handleHoverStart(cardname) {
  clearTimeout(pollTimer);
  showTooltip();

  const cached = cardCache.get(cardname);
  if (cached && cached.status !== 'fetching') {
    renderTooltip(cached);
    return;
  }

  renderTooltip({ status: 'fetching' });
  poll(cardname);
}

function poll(cardname) {
  const step = async () => {
    let body;
    try {
      const res = await fetch(`/api/cards/${encodeURIComponent(cardname)}`);
      body = await res.json();
    } catch (e) {
      pollTimer = setTimeout(step, 600);
      return;
    }
    cardCache.set(cardname, body);
    renderTooltip(body);
    if (body.status === 'fetching') {
      pollTimer = setTimeout(step, 600);
    }
  };
  step();
}

function handleHoverEnd() {
  clearTimeout(pollTimer);
  hideTooltip();
}

function renderTooltip(data) {
  if (data.status === 'ready') {
    if (data.image_url) {
      tooltipEl.innerHTML = '';
      const img = document.createElement('img');
      img.src = data.image_url;
      tooltipEl.appendChild(img);
    } else {
      tooltipEl.textContent = 'No image available';
    }
  } else if (data.status === 'not_found') {
    tooltipEl.textContent = 'Card not found on Scryfall';
  } else {
    tooltipEl.textContent = 'fetching scryfall…';
  }
}

function showTooltip() {
  tooltipEl.classList.remove('hidden');
}

function hideTooltip() {
  tooltipEl.classList.add('hidden');
}

function positionTooltip(event) {
  const offset = 16;
  tooltipEl.style.left = `${event.clientX + offset}px`;
  tooltipEl.style.top = `${event.clientY + offset}px`;
}

loadDecklists();
