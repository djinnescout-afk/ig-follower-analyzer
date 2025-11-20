## Supabase Data Model Proposal

### 1. `clients`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid (PK, default uuid_generate_v4) | Internal identifier |
| `ig_username` | text UNIQUE | Instagram handle (lowercase) |
| `display_name` | text | Friendly name (e.g., client’s real name) |
| `status` | text | enum `pending`, `scraped`, `paused`, `archived` |
| `following_count` | integer | Last known count from Instagram |
| `last_scraped_at` | timestamptz | Last time following list succeeded |
| `last_error` | text | Error message if scrape failed |
| `notes` | text | VA-entered notes |
| `created_at` / `updated_at` | timestamptz | default now() |

Indexes:
- `idx_clients_username` on `lower(ig_username)`

### 2. `pages`
| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid PK | |
| `ig_username` | text UNIQUE | normalized |
| `display_name` | text | profile name |
| `follower_count` | integer | last seen follower count |
| `category` | text | e.g., `BLACK_THEME`, `PERSONAL_BRAND` |
| `category_confidence` | numeric(5,2) | 0-1 |
| `promo_status` | text | `warm`, `unknown`, `not_open` |
| `promo_indicators` | jsonb | array of detected phrases |
| `contact_email` | text | last extracted email |
| `has_contact_form` | boolean | detection flag |
| `pricing_notes` | text | manual price input |
| `last_profile_scraped_at` | timestamptz | |
| `profile_pic_url` | text | fallback URL |
| `profile_pic_storage_path` | text | Supabase storage path for base64 asset |
| `metadata` | jsonb | catch-all for new fields |
| `created_at` / `updated_at` | timestamptz | |

Indexes:
- `idx_pages_username`
- `idx_pages_category`

### 3. `client_following`
Join table linking which pages each client follows.

| Column | Type | Notes |
| --- | --- | --- |
| `client_id` | uuid FK → clients.id | |
| `page_id` | uuid FK → pages.id | |
| `discovered_at` | timestamptz | when the relation was first scraped |
| `last_seen_at` | timestamptz | latest scrape that confirmed it |
| `source_run_id` | uuid FK → scrape_runs.id | optional |

Primary key: `(client_id, page_id)`

### 4. `scrape_runs`
Stores every scrape job (client following or profile scrape) for auditing & coverage.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid PK | |
| `job_type` | text | `client_following`, `profile_scrape`, `categorizer` |
| `target_username` | text | IG handle scraped |
| `client_id` | uuid FK | for following scrapes |
| `status` | text | `queued`, `running`, `succeeded`, `failed` |
| `apify_run_id` | text | reference to Apify job |
| `total_expected` | integer | Instagram’s reported count |
| `total_retrieved` | integer | number of rows saved |
| `coverage_pct` | numeric(5,2) | computed retrieved / expected |
| `failed_accounts` | jsonb | list of usernames that failed in profile scrapes |
| `metadata` | jsonb | misc flags (force, priority, retries) |
| `error_message` | text | failure reason |
| `started_at` / `finished_at` | timestamptz | |

Indexes:
- `idx_scrape_runs_target`
- `idx_scrape_runs_client`
- `idx_scrape_runs_started_at`

### 5. `page_profiles`
Captures detailed profile scrape output (bio, promos, media snapshots).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid PK | |
| `page_id` | uuid FK | |
| `bio` | text | latest bio text |
| `external_url` | text | website link |
| `email_candidates` | jsonb | list of discovered emails |
| `contact_forms` | jsonb | URLs to forms detected |
| `promo_mentions` | jsonb | detection results (keywords, sentences) |
| `posts` | jsonb | last N post metadata (caption, image storage path, likes) |
| `scraped_at` | timestamptz | when snapshot taken |

### 6. `promo_events` (optional)
Record scripted detection events for auditable timeline.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid PK |
| `page_id` | uuid FK |
| `detected_at` | timestamptz |
| `signal_type` | text (`email`, `buy_page`, `promo_link`, etc.) |
| `details` | jsonb |

### Storage & Media
- Use Supabase Storage bucket `page-media` with paths like `profiles/{page_id}/profile_pic.jpg` and `posts/{page_id}/{post_id}.jpg`.
- Keep only references in DB (`storage_path`, `mime_type`) to avoid bloating tables.

### Constraints & Policies
- Enable Row Level Security with service role for API, and user role with policies for VAs (read-only lists, limited writes to notes/status).
- Use triggers to maintain `updated_at` automatically.
- Add Supabase function to compute `clients_following_count` using `client_following` materialized view for faster UI queries.

### Migration Strategy
1. Write `scripts/migrate_clients_json.py` to parse `clients_data.json` and insert into the tables.
2. Populate `clients`, `pages`, `client_following` first.
3. For existing categorization data, store into `page_profiles`, `promo_events`.
4. Backfill `scrape_runs` with synthetic entries so coverage history is preserved.

