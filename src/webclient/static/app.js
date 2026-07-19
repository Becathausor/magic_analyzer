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
const CATEGORY_ORDER = [
  'Creature', 'Planeswalker', 'Battle', 'Instant', 'Sorcery', 'Artifact', 'Enchantment', 'Land', 'Other',
];
const LOADING_CATEGORY = 'Chargement…';

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

    if (zoneKey === 'main_deck') {
      deckViewEl.appendChild(renderMainDeckZone(rows));
      continue;
    }

    const section = document.createElement('section');
    section.className = 'zone';

    const heading = document.createElement('h2');
    heading.textContent = ZONE_LABELS[zoneKey];
    section.appendChild(heading);

    for (const { cardname, quantity } of rows) {
      section.appendChild(createCardRow(cardname, quantity));
    }

    deckViewEl.appendChild(section);
  }
}

function createCardRow(cardname, quantity) {
  const row = document.createElement('div');
  row.className = 'card-row';
  row.textContent = `${quantity} ${cardname}`;
  row.addEventListener('mouseenter', (event) => {
    positionTooltip(event);
    handleHoverStart(cardname);
  });
  row.addEventListener('mousemove', positionTooltip);
  row.addEventListener('mouseleave', handleHoverEnd);
  return row;
}

function renderMainDeckZone(rows) {
  const section = document.createElement('section');
  section.className = 'zone';

  const heading = document.createElement('h2');
  heading.textContent = ZONE_LABELS.main_deck;
  section.appendChild(heading);

  const body = document.createElement('div');
  section.appendChild(body);

  const cardState = new Map();
  for (const { cardname, quantity } of rows) {
    cardState.set(cardname, { quantity, status: 'pending' });
  }

  const renderBody = () => {
    body.innerHTML = '';
    const buckets = new Map();
    const pendingRows = [];

    for (const [cardname, state] of cardState) {
      if (state.status === 'pending') {
        pendingRows.push({ cardname, quantity: state.quantity });
        continue;
      }
      if (state.status === 'not_found') {
        addToBucket(buckets, 'Other', cardname, state.quantity);
        continue;
      }
      addToBucket(buckets, state.category, cardname, state.quantity);
      if (state.opposite_category) {
        addToBucket(buckets, state.opposite_category, null, state.quantity);
      }
    }

    for (const category of CATEGORY_ORDER) {
      const bucket = buckets.get(category);
      if (!bucket) continue;
      body.appendChild(renderCategoryGroup(category, bucket));
    }
    if (pendingRows.length > 0) {
      const pendingCount = pendingRows.reduce((sum, row) => sum + row.quantity, 0);
      body.appendChild(renderCategoryGroup(LOADING_CATEGORY, { count: pendingCount, cards: pendingRows }));
    }
  };

  renderBody();

  for (const { cardname } of rows) {
    fetchCardStatus(cardname).then((data) => {
      const state = cardState.get(cardname);
      if (data.status === 'ready') {
        state.status = 'ready';
        state.category = data.category;
        state.opposite_category = data.opposite_category;
      } else {
        state.status = 'not_found';
      }
      renderBody();
    });
  }

  return section;
}

function addToBucket(buckets, category, cardname, quantity) {
  if (!buckets.has(category)) {
    buckets.set(category, { count: 0, cards: [] });
  }
  const bucket = buckets.get(category);
  bucket.count += quantity;
  if (cardname) {
    bucket.cards.push({ cardname, quantity });
  }
}

function renderCategoryGroup(category, bucket) {
  const group = document.createElement('div');
  group.className = 'category-group';

  const heading = document.createElement('h3');
  heading.textContent = `${category} (${bucket.count})`;
  group.appendChild(heading);

  for (const { cardname, quantity } of bucket.cards) {
    group.appendChild(createCardRow(cardname, quantity));
  }

  return group;
}

async function fetchCardStatus(cardname) {
  const cached = cardCache.get(cardname);
  if (cached && cached.status !== 'fetching') {
    return cached;
  }
  for (;;) {
    let body;
    try {
      const res = await fetch(`/api/cards/${encodeURIComponent(cardname)}`);
      body = await res.json();
    } catch (e) {
      await new Promise((resolve) => setTimeout(resolve, 600));
      continue;
    }
    cardCache.set(cardname, body);
    if (body.status !== 'fetching') {
      return body;
    }
    await new Promise((resolve) => setTimeout(resolve, 600));
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
