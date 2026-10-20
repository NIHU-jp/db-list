'use strict';
(() => {
  const dialog = document.querySelector('#resource-dialog');
  const body = document.querySelector('#dialog-body');
  const institutionDetails = [...document.querySelectorAll('.institution-details')];
  const searchInput = document.querySelector('#directory-query');
  const desktop = window.matchMedia('(min-width: 959px)');
  function adaptDetails() {
    institutionDetails.forEach(details => { details.open = desktop.matches || Boolean(searchInput.value.trim()); });
  }
  institutionDetails.forEach(details => details.querySelector('summary').addEventListener('click', event => {
    if (desktop.matches) event.preventDefault();
  }));
  desktop.addEventListener('change', adaptDetails);
  adaptDetails();
  const searchBox = document.querySelector('.directory-search');
  const searchStatus = document.querySelector('#search-status');
  const searchEmpty = document.querySelector('#search-empty');
  const sections = [...document.querySelectorAll('[data-section]')];
  const normalize = text => text.normalize('NFKC').toLowerCase().replace(/\s+/gu, ' ').trim();
  const entries = [...document.querySelectorAll('[data-entry]')].map(item => {
    const detail = document.getElementById(`detail-${item.dataset.entry}`).content;
    const text = [...detail.querySelectorAll('.dialog-institution, #dialog-title, .dialog-alternate, .dialog-overview p, .dialog-tags')]
      .map(node => node.textContent).join(' ');
    return {item, id: item.dataset.entry, text: normalize(text + ' ' + (item.querySelector(':scope > .list-summary')?.textContent || ''))};
  });
  const total = new Set(entries.map(entry => entry.id)).size;
  const disclosures = [...document.querySelectorAll('.institution-details, .collection-list')];
  let savedDisclosures = null;
  function filterEntries() {
    const terms = normalize(searchInput.value).split(' ').filter(Boolean);
    const active = terms.length > 0;
    if (active && !savedDisclosures) savedDisclosures = new Map(disclosures.map(details => [details, details.open]));
    const matches = new Set();
    entries.forEach(({item, id, text}) => {
      const matchesQuery = terms.every(term => text.includes(term));
      item.hidden = !matchesQuery;
      if (matchesQuery) matches.add(id);
    });
    // Retain ancestor names as context, without counting them as matches.
    entries.forEach(({item}) => {
      if (item.hidden) return;
      for (let parent = item.parentElement.closest('[data-entry]'); parent; parent = parent.parentElement.closest('[data-entry]')) parent.hidden = false;
    });
    sections.forEach(section => { section.hidden = !section.querySelector('[data-entry]:not([hidden])'); });
    if (active) disclosures.forEach(details => {
      const visible = Boolean(details.querySelector('[data-entry]:not([hidden])'));
      details.open = visible;
      if (details.classList.contains('collection-list')) details.hidden = !visible;
    });
    else {
      savedDisclosures?.forEach((wasOpen, details) => { details.open = details.classList.contains('institution-details') ? desktop.matches || wasOpen : wasOpen; });
      savedDisclosures = null;
      disclosures.forEach(details => { details.hidden = false; });
    }
    searchEmpty.hidden = matches.size > 0;
    searchStatus.textContent = searchStatus.dataset.countTemplate.replace('{visible}', matches.size).replace('{total}', total);
  }
  searchInput.addEventListener('input', event => { if (!event.isComposing) filterEntries(); });
  searchInput.addEventListener('compositionend', filterEntries);
  searchInput.addEventListener('search', filterEntries);
  searchBox.hidden = false;
  filterEntries();
  let lastTrigger = null;
  let previousHash = '';
  let currentId = '';


  function open(id, trigger) {
    const template = document.getElementById(`detail-${id}`);
    if (!template || !dialog.showModal) return false;
    if (dialog.open) dialog.close();
    previousHash = location.hash.startsWith('#db-') ? '' : location.hash;
    lastTrigger = trigger && !dialog.contains(trigger) ? trigger : document.querySelector(`[data-entry="${CSS.escape(id)}"] > a`);
    currentId = id;
    body.replaceChildren(template.content.cloneNode(true));
    dialog.showModal();
    document.body.classList.add('dialog-open');
    document.querySelector('#close-dialog').focus();
    return true;
  }
  document.addEventListener('click', event => {
    const anchor = event.target.closest('[data-open]');
    if (!anchor || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (open(anchor.dataset.open, anchor)) {
      event.preventDefault();
      history.pushState(null, '', `#db-${anchor.dataset.open}`);
    }
  });
  document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const rect = dialog.getBoundingClientRect();
    if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
  });
  dialog.addEventListener('close', () => {
    if (dialog.open) return;
    document.body.classList.remove('dialog-open');
    if (location.hash === `#db-${currentId}`) history.replaceState(null, '', `${location.pathname}${location.search}${previousHash}`);
    lastTrigger?.focus({preventScroll: true});
  });
  function fromHash() {
    if (location.hash.startsWith('#db-')) {
      let id;
      try { id = decodeURIComponent(location.hash.slice(4)); } catch { return; }
      if (!dialog.open || currentId !== id) open(id);
    } else if (dialog.open) dialog.close();
  }
  window.addEventListener('popstate', fromHash);
  window.addEventListener('hashchange', fromHash);
  body.addEventListener('click', async event => {
    const button = event.target.closest('[data-copy]');
    if (!button) return;
    const url = new URL(location.href);
    url.hash = `db-${button.dataset.copy}`;
    try {
      await navigator.clipboard.writeText(url.href);
      button.textContent = button.dataset.copiedLabel;
      button.setAttribute('role', 'status');
    } catch {
      // Native prompt leaves a selectable share URL when clipboard access is unavailable.
      window.prompt(document.documentElement.lang === 'ja' ? 'リンクをコピー' : 'Copy link', url.href);
    }
  });
  fromHash();
})();
