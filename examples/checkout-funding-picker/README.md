# Checkout funding-method picker

Static demo UI for ProcureNet v7 `POST /api/v7/sessions/{id}/funding-method`.

Supports:

- **USDC** — with network select (`base`, `arbitrum`, `polygon`, `ethereum`)
- **Card** — binds `method: "card"`
- **ACH** (`bank_transfer`) — `routing_number`, `account_number`, `account_type`, `account_holder_name`
- **ETH wallet** (`eth_wallet`) — `wallet_address` (`0x` + 40 hex), optional `ens_name`, `network` (default `ethereum`)

On submit, the page validates client-side (ABA check digit for ACH; basic hex address for ETH), shows the request JSON, and by default performs a **live** `fetch` POST. Enable **Preview only** to skip the network call.

## Config (localStorage)

| Field | localStorage key | Default |
|---|---|---|
| API base URL | `pn.checkoutFunding.apiBase` | `https://api.procurenet.io` |
| Bearer JWT | `pn.checkoutFunding.jwt` | _(empty)_ |
| Session ID | `pn.checkoutFunding.sessionId` | `sess_demo_001` |
| Preview only | `pn.checkoutFunding.previewOnly` | `0` (live POST) |

Live submit requires a non-empty JWT (`Authorization: Bearer …` + `Content-Type: application/json`). An empty token shows a clear error and does not call the API. No secrets are hardcoded.

The response panel shows HTTP status and body (JSON pretty-printed when possible; raw text otherwise). Network failures are surfaced in the UI.

## Open / serve

From this directory:

```bash
# Option A — open the file directly
open index.html   # macOS
xdg-open index.html   # Linux

# Option B — local static server (recommended; avoids some browser CORS quirks for file://)
python3 -m http.server 8765
# then visit http://localhost:8765/
```

From the Omnipay repo root:

```bash
python3 -m http.server 8765 --directory examples/checkout-funding-picker
```

> **CORS:** the browser will only accept the live response if the API allows your origin. Use Preview only, a local proxy, or an allowed origin when testing against production.

## Files

| File | Role |
|---|---|
| `index.html` | Markup, config fields, form structure |
| `styles.css` | Institutional paper / navy styling |
| `app.js` | Config persistence, ACH/ETH validation, live POST, response panel |

## Related docs

- API: [`api/sessions-funding-method.mdx`](../../api/sessions-funding-method.mdx)
- Guide: [`guides/integrate-checkout.mdx`](../../guides/integrate-checkout.mdx)
- Docs page: [`guides/checkout-funding-picker.mdx`](../../guides/checkout-funding-picker.mdx)
