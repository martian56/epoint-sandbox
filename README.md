# Epoint Sandbox

A local replacement for the [epoint.az](https://epoint.az) payment gateway, so you can build and
test an integration without a merchant account.

```bash
docker run -p 8181:8181 ghcr.io/martian56/epoint-sandbox
```

Postgres is bundled and migrations run on boot. Ready in about 15 seconds.

Point your integration at it:

```
https://epoint.az/api/1/request   ->   http://localhost:8181/api/1/request
```

Every path under `/api/1/` matches production, so nothing else changes.

| URL | |
|---|---|
| `http://localhost:8181` | Dashboard |
| `http://localhost:8181/api/1/*` | Epoint-compatible API |
| `http://localhost:8181/checkout/{token}` | Hosted checkout page |
| `http://localhost:8181/docs` | OpenAPI schema |

## Keys

Two accounts are seeded, so split payments work immediately:

| | Public key | Private key |
|---|---|---|
| Sandbox Merchant | `i000000001` | `sandbox_private_key_0000000001` |
| Split Partner | `i000000002` | `sandbox_private_key_0000000002` |

Or create your own on the **API Management** page: set the website, success, failed and result
URLs, then copy the key pair. Keys use epoint's formats, `i` plus nine digits and a 24 character
secret, so anything validating their shape keeps working in production.

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

Any expiry in the future and any CVV work. The full list is on the Test Cards page and at
`GET /_sandbox/cards`.

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

Every attempt is on the Callbacks page with the payload, the signature, your response and timing.

## Signatures

Epoint signs with `base64(sha1_raw(private_key + data + private_key))`. The digest has to be the
raw 20 bytes, not the hex string, which is where most integrations go wrong.

```python
import base64, hashlib
signature = base64.b64encode(
    hashlib.sha1(f"{private_key}{data}{private_key}".encode()).digest()
).decode()
```

If a request is rejected, paste the pair into the Signature Tool page and it names the mistake.

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

## Running it in staging

The sandbox is usable as a shared service alongside your staging stack, not just on a laptop.

```yaml
services:
  epoint-sandbox:
    image: ghcr.io/martian56/epoint-sandbox:0.1.0
    environment:
      EPOINT_ADMIN_EMAIL: admin@example.com
      EPOINT_ADMIN_PASSWORD: ${EPOINT_ADMIN_PASSWORD}
      EPOINT_PUBLIC_BASE_URL: https://epoint-sandbox.staging.internal
      EPOINT_DATABASE_URL: postgresql+psycopg://epoint:epoint@db:5432/epoint_sandbox
    ports: ['8181:8181']
```

Your services reach it by container name, so `result_url` becomes
`http://your-api:3000/webhooks/epoint` with no `host.docker.internal` involved.

Set `EPOINT_PUBLIC_BASE_URL` to whatever hostname your services use, or the `redirect_url` the API
hands back will point at `localhost` and your checkout redirects will break.

## Authentication

Unset by default, so `docker run` stays a one-liner locally. Set both variables and the dashboard
requires a login:

```bash
docker run -p 8181:8181 \
  -e EPOINT_ADMIN_EMAIL=admin@example.com \
  -e EPOINT_ADMIN_PASSWORD=choose-something \
  ghcr.io/martian56/epoint-sandbox:0.1.0
```

Credentials are read at startup rather than set through a first-run screen, so there is no window
after deploy where an unclaimed instance is waiting to be taken over.

Scripts authenticate with the password as a bearer token instead of a session cookie:

```bash
curl http://localhost:8181/_sandbox/merchants \
  -H "Authorization: Bearer choose-something"
```

`/api/1/*` is unaffected. It is already signature-authenticated, and requiring more would break
the promise that only the base URL and keys change between here and production. `/_sandbox/health`
also stays open so container health checks work without credentials.

Sessions last `EPOINT_SESSION_TTL_HOURS` (12 by default) and are signed with a key derived from the
credentials, so changing the password signs everyone out.

## Security

With no admin password set there is no authentication at all: the dashboard is open and
`GET /_sandbox/merchants` returns private keys in plaintext. The dashboard shows a **No auth** badge
when it is in that state. Fine on `localhost`, not fine on a shared network.

Set a password for anything reachable by other people, and do not expose the sandbox to the public
internet either way. It holds no real money, but it will happily show anyone your callback URLs and
staging hostnames.

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

An independent tool for developers integrating with epoint.az. It imitates the API contract, not
the brand, and processes no real payments.

MIT licensed.
