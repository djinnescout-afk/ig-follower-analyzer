## IG Follower Analyzer API

### Quickstart
```bash
cd api
python -m venv .venv
.venv\Scripts\activate  # or source .venv/bin/activate
pip install -r requirements.txt

cp ../config_example.py .env  # ensure SUPABASE + APIFY keys exist
uvicorn main:app --reload
```

### Environment Variables
| Variable | Description |
| --- | --- |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for server-side operations |
| `APIFY_TOKEN` | Used by worker services to trigger scrapes |

### Endpoints
- `GET /health` – basic heartbeat.
- `GET /api/clients` – list clients.
- `POST /api/clients` – create client.
- `PUT /api/clients/{id}` – update client status/notes.
- `GET /api/pages` – list pages.
- `POST /api/pages` – create page record.
- `PUT /api/pages/{id}` – update categorization fields.
- `POST /api/scrapes` – enqueue a scrape job (`client_following` or `profile_scrape`).
- `GET /api/scrapes/{id}` – fetch scrape run status.

### Next Steps
- Connect Supabase tables defined in `docs/DATA_MODEL_SUPABASE.md`.
- Extend `scrape_runs` service to trigger background workers / Apify webhooks.
- Secure endpoints with Supabase JWT or API keys before exposing publicly.

