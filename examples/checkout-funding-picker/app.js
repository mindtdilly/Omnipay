(function () {
  const DEFAULT_API_BASE = 'https://api.procurenet.io';
  const DEFAULT_SESSION_ID = 'sess_demo_001';

  const LS = {
    apiBase: 'pn.checkoutFunding.apiBase',
    jwt: 'pn.checkoutFunding.jwt',
    sessionId: 'pn.checkoutFunding.sessionId',
    previewOnly: 'pn.checkoutFunding.previewOnly',
  };

  const methodInputs = document.querySelectorAll('input[name="method"]');
  const panels = document.querySelectorAll('[data-panel]');
  const formError = document.getElementById('formError');
  const payloadOut = document.getElementById('payloadOut');
  const payloadBadge = document.getElementById('payloadBadge');
  const endpointPath = document.getElementById('endpointPath');
  const sessionIdDisplay = document.getElementById('sessionIdDisplay');
  const submitBtn = document.getElementById('submitBtn');
  const resetBtn = document.getElementById('resetBtn');
  const apiBaseInput = document.getElementById('apiBase');
  const bearerJwtInput = document.getElementById('bearerJwt');
  const sessionIdInput = document.getElementById('sessionId');
  const previewOnlyInput = document.getElementById('previewOnly');
  const responseBadge = document.getElementById('responseBadge');
  const responseMeta = document.getElementById('responseMeta');
  const responseOut = document.getElementById('responseOut');
  const requestHint = document.getElementById('requestHint');

  function loadConfig() {
    apiBaseInput.value = localStorage.getItem(LS.apiBase) || DEFAULT_API_BASE;
    bearerJwtInput.value = localStorage.getItem(LS.jwt) || '';
    sessionIdInput.value = localStorage.getItem(LS.sessionId) || DEFAULT_SESSION_ID;
    previewOnlyInput.checked = localStorage.getItem(LS.previewOnly) === '1';
    syncEndpoint();
    syncSubmitLabel();
  }

  function persistConfig() {
    localStorage.setItem(LS.apiBase, apiBaseInput.value.trim() || DEFAULT_API_BASE);
    localStorage.setItem(LS.jwt, bearerJwtInput.value.trim());
    localStorage.setItem(LS.sessionId, sessionIdInput.value.trim() || DEFAULT_SESSION_ID);
    localStorage.setItem(LS.previewOnly, previewOnlyInput.checked ? '1' : '0');
  }

  function getConfig() {
    const apiBase = (apiBaseInput.value.trim() || DEFAULT_API_BASE).replace(/\/+$/, '');
    const jwt = bearerJwtInput.value.trim();
    const sessionId = sessionIdInput.value.trim() || DEFAULT_SESSION_ID;
    const previewOnly = previewOnlyInput.checked;
    return { apiBase, jwt, sessionId, previewOnly };
  }

  function syncEndpoint() {
    const { sessionId } = getConfig();
    const path = `/api/v7/sessions/${sessionId}/funding-method`;
    endpointPath.textContent = path;
    sessionIdDisplay.textContent = sessionId;
  }

  function syncSubmitLabel() {
    submitBtn.textContent = previewOnlyInput.checked
      ? 'Preview funding-method request'
      : 'Submit funding method';
    requestHint.textContent = previewOnlyInput.checked
      ? 'Preview only is on — JSON is built locally; no network call.'
      : 'Live POST uses Authorization: Bearer and Content-Type: application/json. Enable Preview only to skip the network call.';
  }

  function selectedMethod() {
    const checked = document.querySelector('input[name="method"]:checked');
    return checked ? checked.value : 'usdc';
  }

  function showPanel(method) {
    panels.forEach((panel) => {
      panel.hidden = panel.dataset.panel !== method;
    });
  }

  function setError(message) {
    if (!message) {
      formError.hidden = true;
      formError.textContent = '';
      return;
    }
    formError.hidden = false;
    formError.textContent = message;
  }


  function isValidEthAddress(addr) {
    if (!/^0x[a-fA-F0-9]{40}$/.test(addr)) return false;
    // Reject all-zero address
    if (/^0x0{40}$/i.test(addr)) return false;
    return true;
  }

  function isValidEnsName(name) {
    if (!name) return true;
    if (name.length < 3 || name.length > 255) return false;
    // Basic ENS-like: labels separated by dots, optional trailing .eth
    return /^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/i.test(name);
  }

  function abaCheckDigitValid(routing) {
    if (!/^\d{9}$/.test(routing)) return false;
    const d = routing.split('').map(Number);
    const sum =
      3 * (d[0] + d[3] + d[6]) +
      7 * (d[1] + d[4] + d[7]) +
      1 * (d[2] + d[5] + d[8]);
    return sum % 10 === 0;
  }

  function buildBody() {
    const method = selectedMethod();
    const body = { method };

    if (method === 'usdc') {
      body.network = document.getElementById('network').value;
      return { ok: true, body };
    }

    if (method === 'card') {
      return { ok: true, body };
    }

    if (method === 'eth_wallet') {
      const wallet_address = document.getElementById('wallet_address').value.trim();
      const ens_name = document.getElementById('ens_name').value.trim();
      const network = document.getElementById('eth_network').value;

      if (!isValidEthAddress(wallet_address)) {
        return {
          ok: false,
          error: 'wallet_address must be 0x followed by exactly 40 hex characters (non-zero).',
        };
      }
      if (ens_name && !isValidEnsName(ens_name)) {
        return {
          ok: false,
          error: 'ens_name must be a valid ENS-like name (3–255 chars, labels and dots).',
        };
      }
      const networks = ['base', 'arbitrum', 'polygon', 'ethereum'];
      if (!networks.includes(network)) {
        return { ok: false, error: 'network must be base, arbitrum, polygon, or ethereum.' };
      }

      body.wallet_address = wallet_address;
      body.network = network;
      if (ens_name) body.ens_name = ens_name;
      return { ok: true, body };
    }

    const routing_number = document.getElementById('routing_number').value.trim();
    const account_number = document.getElementById('account_number').value.trim();
    const account_type = document.getElementById('account_type').value;
    const account_holder_name = document
      .getElementById('account_holder_name')
      .value.trim();

    if (!/^\d{9}$/.test(routing_number)) {
      return { ok: false, error: 'routing_number must be exactly 9 digits (ABA).' };
    }
    if (!abaCheckDigitValid(routing_number)) {
      return {
        ok: false,
        error: 'routing_number failed the ABA check-digit validation.',
      };
    }
    if (!/^\d{4,17}$/.test(account_number)) {
      return { ok: false, error: 'account_number must be 4–17 digits.' };
    }
    if (account_type !== 'checking' && account_type !== 'savings') {
      return { ok: false, error: 'account_type must be checking or savings.' };
    }
    if (account_holder_name.length < 2 || account_holder_name.length > 100) {
      return {
        ok: false,
        error: 'account_holder_name must be between 2 and 100 characters.',
      };
    }

    body.routing_number = routing_number;
    body.account_number = account_number;
    body.account_type = account_type;
    body.account_holder_name = account_holder_name;
    return { ok: true, body };
  }

  function resetResponse() {
    responseBadge.textContent = '—';
    responseBadge.className = 'badge';
    responseMeta.textContent = 'No response yet.';
    responseOut.textContent = '{ /* submit to see status and body */ }';
  }

  function renderRequest(body) {
    payloadOut.textContent = JSON.stringify(body, null, 2);
  }

  function formatResponseBody(text) {
    const trimmed = (text || '').trim();
    if (!trimmed) return '(empty body)';
    try {
      return JSON.stringify(JSON.parse(trimmed), null, 2);
    } catch {
      return trimmed;
    }
  }

  async function submitLive(body, config) {
    const url = `${config.apiBase}/api/v7/sessions/${encodeURIComponent(config.sessionId)}/funding-method`;
    payloadBadge.textContent = 'Sending';
    payloadBadge.className = 'badge';
    responseBadge.textContent = '…';
    responseBadge.className = 'badge';
    responseMeta.textContent = `POST ${url}`;
    responseOut.textContent = '{ /* waiting */ }';
    submitBtn.disabled = true;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${config.jwt}`,
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(body),
      });

      const raw = await res.text();
      const pretty = formatResponseBody(raw);
      responseMeta.textContent = `HTTP ${res.status} ${res.statusText || ''} · ${url}`.trim();
      responseOut.textContent = pretty;
      responseBadge.textContent = String(res.status);
      responseBadge.className = res.ok ? 'badge ok' : 'badge err';
      payloadBadge.textContent = res.ok ? 'Sent' : 'Sent (error)';
      payloadBadge.className = res.ok ? 'badge ok' : 'badge err';
    } catch (err) {
      const message = err && err.message ? err.message : String(err);
      responseBadge.textContent = 'Network';
      responseBadge.className = 'badge err';
      responseMeta.textContent = `Network error · ${url}`;
      responseOut.textContent = message;
      payloadBadge.textContent = 'Failed';
      payloadBadge.className = 'badge err';
      setError(`Network error: ${message}`);
    } finally {
      submitBtn.disabled = false;
    }
  }

  async function onSubmit() {
    persistConfig();
    syncEndpoint();
    const config = getConfig();
    const result = buildBody();

    if (!result.ok) {
      setError(result.error);
      payloadBadge.textContent = 'Invalid';
      payloadBadge.className = 'badge err';
      payloadOut.textContent = '{\n  /* fix validation errors, then submit again */\n}';
      resetResponse();
      return;
    }

    setError('');
    renderRequest(result.body);

    if (config.previewOnly) {
      payloadBadge.textContent = 'Preview';
      payloadBadge.className = 'badge ok';
      responseBadge.textContent = 'Skipped';
      responseBadge.className = 'badge';
      responseMeta.textContent = 'Preview only — no network call.';
      responseOut.textContent = '{ /* preview mode */ }';
      console.info('[checkout-funding-picker] preview POST', {
        url: `${config.apiBase}/api/v7/sessions/${config.sessionId}/funding-method`,
        body: result.body,
      });
      return;
    }

    if (!config.jwt) {
      setError('Bearer JWT is required for live POST. Paste a token, or enable Preview only.');
      payloadBadge.textContent = 'Blocked';
      payloadBadge.className = 'badge err';
      resetResponse();
      responseMeta.textContent = 'Blocked — empty JWT.';
      responseOut.textContent = '{ /* set Bearer JWT or enable Preview only */ }';
      return;
    }

    if (!config.apiBase) {
      setError('API base URL is required.');
      payloadBadge.textContent = 'Blocked';
      payloadBadge.className = 'badge err';
      return;
    }

    await submitLive(result.body, config);
  }

  methodInputs.forEach((input) => {
    input.addEventListener('change', () => {
      showPanel(selectedMethod());
      setError('');
    });
  });

  [apiBaseInput, bearerJwtInput, sessionIdInput].forEach((el) => {
    el.addEventListener('change', () => {
      persistConfig();
      syncEndpoint();
    });
    el.addEventListener('input', () => {
      if (el === sessionIdInput || el === apiBaseInput) syncEndpoint();
    });
  });

  previewOnlyInput.addEventListener('change', () => {
    persistConfig();
    syncSubmitLabel();
  });

  submitBtn.addEventListener('click', () => {
    onSubmit();
  });

  resetBtn.addEventListener('click', () => {
    document.querySelector('input[name="method"][value="usdc"]').checked = true;
    document.getElementById('network').value = 'base';
    document.getElementById('routing_number').value = '';
    document.getElementById('account_number').value = '';
    document.getElementById('account_type').value = 'checking';
    document.getElementById('account_holder_name').value = '';
    document.getElementById('wallet_address').value = '';
    document.getElementById('ens_name').value = '';
    document.getElementById('eth_network').value = 'ethereum';
    showPanel('usdc');
    setError('');
    payloadBadge.textContent = 'Idle';
    payloadBadge.className = 'badge';
    payloadOut.textContent = '{ /* choose a method and submit */ }';
    resetResponse();
  });

  loadConfig();
  showPanel(selectedMethod());
})();
