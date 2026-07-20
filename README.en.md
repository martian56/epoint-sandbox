[Azərbaycanca](README.md) · **English**

# Epoint Sandbox

A local replacement for the [epoint.az](https://epoint.az) payment gateway, so you can build and
test an integration without a merchant account.

```bash
docker run -p 8181:8181 ghcr.io/martian56/epoint-sandbox
```

Point your integration at it:

```
https://epoint.az/api/1/request   ->   http://localhost:8181/api/1/request
```

Every path under `/api/1/` matches production, so nothing else changes.

![The sandbox dashboard, a copy of the epoint merchant cabinet](images/dashboard.png)

| URL | |
|---|---|
| `http://localhost:8181` | Dashboard |
| `http://localhost:8181/api/1/*` | Epoint-compatible API |
| `http://localhost:8181/checkout/{token}` | Hosted checkout page |
| `http://localhost:8181/docs` | OpenAPI schema |

## What you get

**Every payment lands somewhere you can see it.** The dashboard is a copy of epoint's, so what you
learn here transfers. Transactions, a real balance ledger, saved cards, invoices, bank transfers,
plus a request log and callback inspector that production has no equivalent for.

**Failures on demand.** Epoint publishes no test cards, so the sandbox defines its own. The last
three digits are the bank response code, so reading the number tells you what will happen. Want to
test the declined path, or a gateway timeout where no callback ever arrives? Type a different
number.

![The test card catalogue](images/test-cards.png)

**The signature mistake, named.** Epoint signs with `base64(sha1_raw(private_key + data +
private_key))`, and the digest has to be the raw 20 bytes rather than the hex string. That single
detail accounts for most failed integrations. Paste a failing pair in and the tool tells you which
mistake you made.

![The signature tool diagnosing a hex digest mistake](images/signature-tool.png)

**Callbacks you can actually watch.** The sandbox posts to your `result_url` with the same signed
payload production sends. Every attempt is recorded with the decoded payload, the raw `data`, the
signature and your own response, so a webhook that quietly 500s is visible rather than mysterious.

![A callback attempt with its decoded payload and signature](images/callbacks.png)

**Keys and grants you control.** Rotate a private key and existing signatures stop verifying,
exactly as in production. AMEX, Apple Pay, Google Pay, installments, wallets and B2B are off by
default, because epoint grants them per merchant on request, so an integration meets the same
refusal here that it would on go-live.

![API management with keys, integration URLs and feature grants](images/api-management.png)

**The hosted checkout page**, which is where your customer actually pays.

![The hosted checkout page](images/checkout.png)

**Apple Pay and Google Pay**, served as a widget you embed rather than redirect to, answering with
a `postMessage` the way production does.

![The wallet widget embedded in a merchant page](images/wallet-widget.png)

## Local development

Two accounts are seeded, so split payments work immediately:

| | Public key | Private key |
|---|---|---|
| Sandbox Merchant | `i000000001` | `sandbox_private_key_0000000001` |
| Split Partner | `i000000002` | `sandbox_private_key_0000000002` |

Or create your own on the **API Management** page: set the website, success, failed and result
URLs, then copy the key pair. Keys use epoint's formats, `i` plus nine digits and a 24 character
secret, so anything validating their shape keeps working in production.

A typical loop:

```bash
docker run -d -p 8181:8181 --name epoint \
  --add-host=host.docker.internal:host-gateway \
  ghcr.io/martian56/epoint-sandbox
```

Point your `result_url` at your own machine. Callbacks originate inside the container, so
`localhost` there means the container, not you:

```bash
curl -X PATCH http://localhost:8181/_sandbox/merchants/i000000001 \
  -H "Content-Type: application/json" \
  -d '{"result_url": "http://host.docker.internal:3000/webhooks/epoint"}'
```

Then drive a payment: POST to `/api/1/request`, redirect to the `redirect_url` you get back, pay
with `4111 1111 1111 1111`, and watch the callback arrive. When something fails, the Request Log
page has the raw `data`, the signature and whether it verified; the Callbacks page has every
delivery attempt with your response body.

There is no login locally. Every restart is a clean database unless you mount a volume.

## Test cards

The last three digits are the bank response code.

| Card | Result |
|---|---|
| `4111 1111 1111 1111` | Approved (`000`) |
| `4000 0000 0000 0116` | Insufficient funds (`116`) |
| `4000 0000 0000 0101` | Card expired (`101`) |
| `4000 0000 0000 0102` | Suspected fraud (`102`) |
| `4000 0000 0000 0209` | Stolen card (`209`) |
| `4000 0000 0000 3220` | Approved after a 3DS challenge |
| `4000 0000 0000 9999` | Gateway timeout, no callback sent |

Any expiry in the future and any CVV work. The full list is at `GET /_sandbox/cards`.

## Callbacks

The sandbox posts to your `result_url` with the same `data` and `signature` pair production uses.
Set it on the API Management page, or through the API:

```bash
curl -X PATCH http://localhost:8181/_sandbox/merchants/i000000001 \
  -H "Content-Type: application/json" \
  -d '{"result_url": "http://host.docker.internal:3000/webhooks/epoint"}'
```

Callbacks originate inside the container, so `localhost` there is the container, not your machine.
Use `host.docker.internal`. On Linux that host has to be added:

```bash
docker run -p 8181:8181 --add-host=host.docker.internal:host-gateway \
  ghcr.io/martian56/epoint-sandbox
```

## Signatures

Epoint signs with `base64(sha1_raw(private_key + data + private_key))`. The digest has to be the
raw 20 bytes, not the hex string, which is where most integrations go wrong.

```python
import base64, hashlib
signature = base64.b64encode(
    hashlib.sha1(f"{private_key}{data}{private_key}".encode()).digest()
).decode()
```

The Signature Tool page takes a failing pair and names the mistake.

## Endpoints

All 30 documented endpoints are implemented.

| Area | Endpoints |
|---|---|
| Checkout | `request`, `checkout`, `payment-request`, `amex-request`, `payment-change-sum` |
| Split | `split-request`, `split-execute-pay` |
| Pre-auth | `pre-auth-request`, `pre-auth-complete` |
| Cards | `card-registration`, `card-registration-with-pay`, `execute-pay`, `get-status-card` |
| Money | `refund-request` (refund and payout), `reverse` |
| Status | `get-status` |
| Invoices | `create`, `update`, `view`, `list`, `send-sms`, `send-email` |
| Installments | `get-installment-request`, `installment-request` |
| Wallet | `wallet/status`, `wallet/payment` |
| Token | `token/widget` |
| B2B | `b2b/payment`, `b2b/payment/{order_id}` |
| Health | `heartbeat` |

### Apple Pay and Google Pay

Both run through `token/widget`, which returns a `widget_url` you embed rather than redirect to.
One widget serves both wallets; the device decides which button it can show.

```html
<iframe src="{widget_url}" width="100%" height="330"></iframe>
```

The result arrives as a `postMessage` to the page hosting the iframe, not as a redirect:

```js
window.addEventListener('message', (event) => {
  // { status: 'success', payment: { order_id, transaction, card_mask, ... } }
})
```

The signed callback to your `result_url` still fires, and it is the one to settle the order on.
Inside the sandbox widget you can pick which test card the wallet holds, so declines are reachable.

Balances are a real ledger: payments credit, commission and refunds debit, splits move between
accounts. Invoice SMS and email are captured in the dashboard rather than delivered.

AMEX, Apple Pay, Google Pay, installments, wallets and B2B are off by default, because epoint
grants them per merchant on request. Turn them on from API Management.

Every response carries `X-Epoint-Sandbox: 1`. Assert its absence in your production smoke tests.

## Configuration

| Variable | |
|---|---|
| `EPOINT_DATABASE_URL` | Use your own Postgres instead of the bundled one |
| `EPOINT_PUBLIC_BASE_URL` | Base for the `redirect_url` values handed back to you, default `http://localhost:8181` |
| `EPOINT_ADMIN_EMAIL` / `EPOINT_ADMIN_PASSWORD` | Set both to require a dashboard login. Unset means open. |
| `EPOINT_SESSION_TTL_HOURS` | How long a dashboard session lasts, default `12` |
| `EPOINT_COMMISSION_RATE` | Commission taken on settlement, default `0.03` |
| `EPOINT_SEED_MERCHANTS` | Set `false` to start with no accounts |

Bundled data lives at `/var/lib/postgresql/data`. Mount a volume there to keep it between
containers.

## Staging

The same container runs as a shared service next to your staging stack. Set an admin password and
the dashboard requires a login.

```yaml
services:
  epoint-sandbox:
    image: ghcr.io/martian56/epoint-sandbox:latest
    environment:
      EPOINT_ADMIN_EMAIL: admin@example.com
      EPOINT_ADMIN_PASSWORD: ${EPOINT_ADMIN_PASSWORD}
      EPOINT_PUBLIC_BASE_URL: https://epoint-sandbox.staging.internal
      EPOINT_DATABASE_URL: postgresql+psycopg://epoint:epoint@db:5432/epoint_sandbox
    ports: ['8181:8181']
```

Three things change compared to local.

**Your services reach it by container name.** `result_url` becomes
`http://your-api:3000/webhooks/epoint`, with no `host.docker.internal` involved.

**`EPOINT_PUBLIC_BASE_URL` has to be set.** The `redirect_url` the API hands back is built from it.
Leave it at the default and your checkout redirects will send customers to `localhost`.

**The seeded keys are generated, not the published ones.** The keys in the table above ship in the
public image, so a secured instance issues random ones instead. The public keys stay `i000000001`
and `i000000002` so split payments still work, but the secrets are unique to your deployment. Read
them from the API Management page after your first login.

That last point matters: the login gate protects the dashboard and `/_sandbox/*`, but `/api/1/*` is
signature-authenticated only. If it kept the published secrets, anyone who could reach the sandbox
could sign valid requests and push fake payment callbacks into your staging system.

### Signing in

Credentials are read at startup rather than claimed through a first-run screen, so there is no
window after deploy where an unclaimed instance is waiting to be taken over.

Scripts use the password as a bearer token instead of a session cookie:

```bash
curl https://epoint-sandbox.staging.internal/_sandbox/merchants \
  -H "Authorization: Bearer $EPOINT_ADMIN_PASSWORD"
```

Sessions last `EPOINT_SESSION_TTL_HOURS`, 12 by default, and are signed with a key derived from the
credentials, so changing the password signs everyone out.

`/_sandbox/health` stays open so container health checks work without credentials.

## Security

`/api/1/*` is never gated by the admin password. It is already signature-authenticated, and
requiring more would break the promise that only the base URL and keys change between here and
production. Protect it by keeping the sandbox off untrusted networks, not by adding a second layer.

With no admin password set there is no authentication at all: the dashboard is open and
`GET /_sandbox/merchants` returns private keys in plaintext. The dashboard shows a **No auth** badge
in the header when it is in that state. Fine on `localhost`, not fine anywhere else.

Do not expose the sandbox to the public internet either way. It holds no real money, but it will
show anyone your callback URLs and staging hostnames.

## Contributing

Requires [bun](https://bun.sh) and [uv](https://docs.astral.sh/uv/).

```bash
bun install
docker compose up -d
cd apps/api && uv sync && uv run alembic upgrade head && cd ../..

bun run dev:api    # API on 8181
bun run dev:web    # dashboard on 5173
```

`bun run check` runs everything CI does. `bun run tokens` regenerates the design tokens after
editing `design-tokens.json`.

## Not affiliated with Epoint

An independent tool for developers integrating with epoint.az. It imitates the API contract and processes no real payments.

MIT licensed.
