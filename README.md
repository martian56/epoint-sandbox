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
| `EPOINT_COMMISSION_RATE` | Commission taken on settlement, default `0.03` |
| `EPOINT_SEED_MERCHANTS` | Set `false` to start with no accounts |

Bundled data lives at `/var/lib/postgresql/data`. Mount a volume there to keep it between
containers.

## Security

There is no authentication. The dashboard is open and `GET /_sandbox/merchants` returns private
keys in plaintext. That is fine on `localhost`, which is the only place it is meant to run. Do not
publish port 8181 to a network.

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
