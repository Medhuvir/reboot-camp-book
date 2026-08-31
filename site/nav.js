// site/nav.js — shared hamburger-menu behavior, loaded on every page.
(function () {
  var nav = document.getElementById('landing-nav');
  var toggle = document.getElementById('nav-toggle');
  var closeBtn = document.getElementById('nav-close');
  var overlay = document.getElementById('nav-overlay');
  if (!nav || !toggle) return;

  function openMenu() {
    nav.classList.add('nav-open');
    if (overlay) overlay.classList.add('nav-open');
    toggle.setAttribute('aria-expanded', 'true');
  }
  function closeMenu() {
    nav.classList.remove('nav-open');
    if (overlay) overlay.classList.remove('nav-open');
    toggle.setAttribute('aria-expanded', 'false');
  }
  function toggleMenu() {
    if (nav.classList.contains('nav-open')) {
      closeMenu();
    } else {
      openMenu();
    }
  }

  toggle.addEventListener('click', toggleMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMenu);
  if (overlay) overlay.addEventListener('click', closeMenu);
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && nav.classList.contains('nav-open')) closeMenu();
  });
})();
