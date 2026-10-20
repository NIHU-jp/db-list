'use strict';
(() => {
  const dialog = document.querySelector('#resource-dialog');
  const body = document.querySelector('#dialog-body');
  const institutionDetails = [...document.querySelectorAll('.institution-details')];
  const desktop = window.matchMedia('(min-width: 959px)');
  function adaptDetails() {
    institutionDetails.forEach(details => { details.open = desktop.matches; });
  }
  institutionDetails.forEach(details => details.querySelector('summary').addEventListener('click', event => {
    if (desktop.matches) event.preventDefault();
  }));
  desktop.addEventListener('change', adaptDetails);
  adaptDetails();
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
  document.querySelectorAll('[data-language-switch]').forEach(anchor => anchor.addEventListener('click', () => {
    const url = new URL(anchor.getAttribute('href'), location.href);
    if (location.hash.startsWith('#db-')) url.hash = location.hash;
    anchor.href = url.href;
  }));
  fromHash();
})();
