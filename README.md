# Web Data Scrape

A small Django/DRF service that renders web pages with Playwright and returns
selected DOM elements by CSS class name.

## API

`GET /scrape/data/`

Required query parameters:

- `url`: an `http` or `https` URL.
- `class_name`: a CSS class to extract. Repeat the parameter to extract more
  than one class.

Required headers:

- `X-Client-ID`
- `X-Client-Secret`

Example:

```bash
curl -G 'http://localhost:8080/scrape/data/' \
  --data-urlencode 'url=https://example.com/' \
  --data-urlencode 'class_name=item' \
  -H "X-Client-ID: $CLIENT_ID" \
  -H "X-Client-Secret: $CLIENT_SECRET"
```

A successful response has the form:

```json
{"scraped_data": [{"tag": "div", "text": "Example", "attributes": {"class": ["item"]}, "children": []}]}
```

Errors use a consistent envelope and may include validation details:

```json
{"error": "Invalid request parameters.", "details": {"url": ["Enter a valid URL."]}}
```

Status codes:

- `400`: invalid parameters or a disallowed URL.
- `401`: missing, invalid, inactive, or expired client credentials.
- `429`: client rate limit exceeded.
- `502`: the target could not be fetched or parsed.
- `504`: the target timed out.

Extraction is bounded by configurable depth, node, element, HTML-size, and
per-client rate limits. The API accepts class names only; it does not execute
arbitrary CSS selectors, paginate, or expose a proxy endpoint.

## Local setup

Python 3.11 and PostgreSQL are expected.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
playwright install chromium
```

Copy the environment template and replace the placeholder secrets:

```bash
cp .env.example .env
```

For a local PostgreSQL instance, set `POSTGRES_HOST` and `POSTGRES_PORT` in
`.env` as appropriate. Then run migrations and start the server:

```bash
python manage.py migrate
python manage.py runserver
```

Create an API client and save the printed secret; it is not stored in plain
text and cannot be shown again:

```bash
python manage.py create_client "My Application"
```

Rotate a secret if it may have been exposed:

```bash
python manage.py rotate_client_secret <client_id>
```

## Docker Compose

```bash
cp .env.example .env
# edit .env and replace DJANGO_SECRET_KEY and POSTGRES_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(50))"
docker compose up --build
```

The web container runs migrations on startup by default. Set
`RUN_MIGRATIONS=0` if migrations are managed separately. PostgreSQL is not
published to the host by default.

## Tests

The test suite uses SQLite and mocked browser transport, so it does not require
PostgreSQL or a downloaded Chromium build:

```bash
pytest -q
flake8 app tests
python manage.py check --settings=app.test_settings
```

CI runs the suite on Python 3.11. Real Playwright and PostgreSQL integration
tests are not part of this suite.

## Configuration

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Django secret; required | none |
| `DJANGO_DEBUG` | Enable debug mode | `False` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts | `127.0.0.1,localhost` |
| `DJANGO_LOG_LEVEL` | Application log level | `INFO` |
| `POSTGRES_DB` / `POSTGRES_USER` / `POSTGRES_PASSWORD` | Database credentials | none |
| `POSTGRES_HOST` / `POSTGRES_PORT` | Database address | unset (local socket) / `5432` |
| `SCRAPE_THROTTLE_RATE` | DRF rate limit per client | `60/min` |
| `SCRAPE_REQUEST_TIMEOUT_SECONDS` | Static request timeout | `30` |
| `SCRAPE_PAGE_TIMEOUT_MS` | Playwright navigation timeout | `30000` |
| `SCRAPE_MAX_HTML_BYTES` | Maximum rendered HTML size | `5000000` |
| `SCRAPE_MAX_EXTRACTION_DEPTH` | Maximum DOM depth per match | `50` |
| `SCRAPE_MAX_EXTRACTION_NODES` | Maximum DOM nodes per match | `10000` |
| `SCRAPE_MAX_ELEMENTS` | Maximum matched elements per request | `1000` |

Rate limits use Django's configured cache. The default local-memory cache is
per-process; configure a shared cache backend if the service runs multiple
workers or replicas.

## Security notes

The URL validator rejects non-HTTP(S) schemes, embedded credentials, localhost,
private/link-local/reserved addresses, and hostnames that resolve only to
non-public addresses. Playwright route interception checks redirects and page
subresources. These are application-level controls and do not replace network
egress policies, which are still recommended to address DNS rebinding and
non-HTTP protocols.

## License

See [LICENSE](LICENSE).
