// Shared ebook/newsletter signup: modal open/close, native form submit via
// /api/subscribe (netlify/functions/subscribe.js), and the in-modal
// "ebook sent" confirmation. Used by every page with #ebook-modal or a
// .signup-form.
(function() {
  var modal = document.getElementById('ebook-modal');
  var closeBtn = document.getElementById('ebook-modal-close');
  var backdrop = document.getElementById('ebook-modal-backdrop');
  var lastFocus = null;

  function views() {
    return modal ? modal.querySelectorAll('.ebook-modal-view') : [];
  }

  function setView(name) {
    if (!modal) return;
    Array.prototype.forEach.call(views(), function(v) {
      v.hidden = v.getAttribute('data-view') !== name;
    });
    modal.setAttribute('aria-labelledby', name === 'success' ? 'ebook-modal-success-title' : 'ebook-modal-title');
  }

  function openModal(view) {
    if (!modal) return;
    view = view || 'form';
    if (!modal.classList.contains('is-open')) lastFocus = document.activeElement;
    setView(view);
    modal.classList.add('is-open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    var target = view === 'success'
      ? document.getElementById('ebook-modal-success-title')
      : modal.querySelector('.signup-input');
    if (target) target.focus();
  }

  function closeModal() {
    if (!modal) return;
    modal.classList.remove('is-open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    setView('form');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  if (modal) {
    document.querySelectorAll('.ebook-signup-trigger').forEach(function(el) {
      el.addEventListener('click', function() { openModal('form'); });
    });
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (backdrop) backdrop.addEventListener('click', closeModal);
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.classList.contains('is-open')) closeModal();
    });
  }

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  document.querySelectorAll('.signup-form').forEach(function(form) {
    var submit = form.querySelector('.signup-submit');
    var error = form.querySelector('.signup-error');
    var submitLabel = submit ? submit.textContent : '';

    function showError(msg) {
      if (!error) return;
      error.textContent = msg;
      error.hidden = !msg;
    }

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      var email = form.elements.email.value.trim();
      if (!EMAIL_RE.test(email)) {
        showError('Please enter a valid email address.');
        form.elements.email.focus();
        return;
      }
      showError('');
      submit.disabled = true;
      submit.textContent = 'Sending…';

      fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          first_name: form.elements.first_name.value,
          last_name: form.elements.last_name.value,
          email: email,
          company: form.elements.company.value,
          page: window.location.href
        })
      })
        .then(function(res) {
          return res.json().catch(function() { return {}; }).then(function(body) {
            if (!res.ok) throw new Error(body.error || 'Something went wrong. Please try again in a moment.');
          });
        })
        .then(function() {
          form.reset();
          openModal('success');
        })
        .catch(function(err) {
          // TypeError = network failure (fetch rejected); anything else carries the server's message
          showError(err instanceof TypeError || !err.message ? 'Something went wrong. Please try again in a moment.' : err.message);
        })
        .then(function() {
          submit.disabled = false;
          submit.textContent = submitLabel;
        });
    });
  });
})();
