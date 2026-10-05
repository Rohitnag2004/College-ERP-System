(function () {
  'use strict';

  const configuredIdleSeconds = Number(document.body.dataset.idleTimeoutSeconds);
  const IDLE_LIMIT = (Number.isFinite(configuredIdleSeconds) && configuredIdleSeconds > 0 ? configuredIdleSeconds : 300) * 1000;
  const ACTIVITY_PING_INTERVAL = 60 * 1000;
  let lastActivity = Date.now();
  let idleTimer;
  let loadingRequests = 0;
  let logoutStarted = false;

  const bar = document.createElement('div');
  bar.id = 'portal-loading-bar';
  bar.setAttribute('role', 'progressbar');
  bar.setAttribute('aria-label', 'Loading');
  document.body.appendChild(bar);

  function showLoading() {
    loadingRequests += 1;
    bar.classList.add('is-active');
  }

  function hideLoading() {
    loadingRequests = Math.max(0, loadingRequests - 1);
    if (!loadingRequests) bar.classList.remove('is-active');
  }

  if (window.jQuery) {
    window.jQuery(document).on('ajaxStart.portalUX', showLoading);
    window.jQuery(document).on('ajaxStop.portalUX', function () {
      loadingRequests = 0;
      bar.classList.remove('is-active');
    });
  }

  document.addEventListener('submit', function (event) {
    const button = event.submitter || event.target.querySelector('button[type="submit"], input[type="submit"]');
    if (!button || button.dataset.loadingShown === 'true') return;
    button.dataset.loadingShown = 'true';
    button.setAttribute('aria-busy', 'true');
    const spinner = document.createElement('span');
    spinner.className = 'spinner-border portal-button-spinner me-2';
    spinner.setAttribute('aria-hidden', 'true');
    button.prepend(spinner);
  }, true);

  function logoutForIdle() {
    if (logoutStarted) return;
    logoutStarted = true;
    const csrf = document.querySelector('form[action$="logout_user/"] input[name="csrfmiddlewaretoken"]');
    const logoutForm = csrf && csrf.form;
    const payload = new FormData();
    if (csrf) payload.append('csrfmiddlewaretoken', csrf.value);
    fetch(logoutForm ? logoutForm.action : '/logout_user/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: csrf ? { 'X-CSRFToken': csrf.value } : {},
      body: payload,
      keepalive: true
    }).finally(function () {
      window.location.replace(document.body.dataset.loginUrl || '/');
    });
  }

  function scheduleIdleLogout() {
    window.clearTimeout(idleTimer);
    idleTimer = window.setTimeout(function () {
      if (Date.now() - lastActivity >= IDLE_LIMIT) logoutForIdle();
      else scheduleIdleLogout();
    }, IDLE_LIMIT);
  }

  let lastStoredActivity = 0;
  function recordActivity() {
    const now = Date.now();
    if (now - lastActivity >= IDLE_LIMIT) {
      logoutForIdle();
      return;
    }
    lastActivity = now;
    if (now - lastStoredActivity > 5000) {
      lastStoredActivity = now;
      try { localStorage.setItem('vtu-portal-last-activity', String(now)); } catch (error) { /* Storage is optional. */ }
    }
    scheduleIdleLogout();
  }

  function enforceIdleOnResume() {
    if (Date.now() - lastActivity >= IDLE_LIMIT) logoutForIdle();
    else scheduleIdleLogout();
  }

  ['click', 'keydown', 'touchstart', 'pointerdown', 'scroll', 'input', 'wheel'].forEach(function (eventName) {
    document.addEventListener(eventName, recordActivity, { passive: true, capture: true });
  });
  let lastMouseMove = 0;
  document.addEventListener('mousemove', function () {
    if (Date.now() - lastMouseMove < 1000) return;
    lastMouseMove = Date.now();
    recordActivity();
  }, { passive: true });
  window.addEventListener('storage', function (event) {
    if (event.key !== 'vtu-portal-last-activity') return;
    const sharedActivity = Number(event.newValue);
    if (Number.isFinite(sharedActivity) && sharedActivity > lastActivity) {
      lastActivity = sharedActivity;
      scheduleIdleLogout();
    }
  });
  window.addEventListener('focus', enforceIdleOnResume);
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'visible') enforceIdleOnResume();
  });
  scheduleIdleLogout();

  window.setInterval(function () {
    if (Date.now() - lastActivity >= IDLE_LIMIT) return;
    const csrf = document.querySelector('form[action$="logout_user/"] input[name="csrfmiddlewaretoken"]');
    const body = new URLSearchParams();
    if (csrf) body.set('csrfmiddlewaretoken', csrf.value);
    body.set('last_activity', String(lastActivity / 1000));
    fetch(document.body.dataset.sessionActivityUrl || '/session-activity/', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
        'X-Requested-With': 'XMLHttpRequest',
        ...(csrf ? { 'X-CSRFToken': csrf.value } : {})
      },
      body: body.toString()
    }).then(function (response) {
      if (response.status === 401) window.location.replace(document.body.dataset.loginUrl || '/');
    }).catch(function () { /* A failed heartbeat is handled by the server idle timeout. */ });
  }, ACTIVITY_PING_INTERVAL);
})();
