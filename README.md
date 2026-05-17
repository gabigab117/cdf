# Comité des Fêtes — Backoffice

> Backoffice for a local festival committee, built with Django 6, Wagtail 7, Tailwind CSS 4 and HTMX.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![Django](https://img.shields.io/badge/django-6.0-green)
![Wagtail](https://img.shields.io/badge/wagtail-7.3-43b1b0)
![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Features

| App | Description |
|-----|-------------|
| [`core/`](core/) | Extended Wagtail document model with date and notes fields |
| [`events/`](events/) | Wagtail pages for event listing and detail, HTMX-powered volunteer station management |
| [`equipment/`](equipment/) | Inventory tracking and equipment loan management |
| [`ia/`](ia/) | AI document summarization and analysis via Mistral AI |
| [`home/`](home/) | Home page (placeholder) |
| [`search/`](search/) | Full-text Wagtail search (placeholder) |

The event index is public. Detail pages are access-controlled via Wagtail `PageViewRestriction`. All management interfaces are restricted to **moderators** (superusers or members of the `Moderators` group).

## Prerequisites

- Python 3.12+
- Node 18+
- Git

## Quick Start

```sh
git clone <repo-url>
cd cdf

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then edit .env with your values

python manage.py migrate
python manage.py createsuperuser

npm install
```

Then start both processes:

```sh
# Terminal 1 — Tailwind (watch)
npm run dev

# Terminal 2 — Django
python manage.py runserver
```

Wagtail admin: <http://localhost:8000/admin/>

## Environment Variables

Copy [`.env.example`](.env.example) to `.env` and fill in the required values.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | — | Django secret key |
| `DEBUG` | No | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | No | `*` | Comma-separated list of allowed hosts |
| `WAGTAILADMIN_BASE_URL` | No | `http://localhost:8000` | Base URL used in Wagtail admin emails |
| `MISTRAL_API_KEY` | **Yes** | — | API key for Mistral AI ([get one](https://console.mistral.ai/)) |
| `DB_NAME` | Prod only | — | MySQL database name |
| `DB_USER` | Prod only | — | MySQL user |
| `DB_PASSWORD` | Prod only | — | MySQL password |

Development uses **SQLite** by default. Production uses **MySQL** — set the three `DB_*` variables accordingly.

## How It Works

### Documents (`core/`)

[`CustomDocument`](core/models.py) extends Wagtail's `AbstractDocument` with a `document_date` and a `notes` field. Documents are organised with native Wagtail collections (no custom category model). Accepted file types: csv, docx, odt, pdf, pptx, rtf, txt, xlsx, zip.

### Events (`events/`)

- [`EventIndexPage`](events/models.py) — lists child `EventPage` items with configurable pagination. Exposes a `can_view_details` flag: only Wagtail editors/moderators see the detail link.
- [`EventPage`](events/models.py) — event detail with date, rich-text notes (StreamField), attached images and documents grouped by collection.

**Volunteer stations** — each event can have stations (`EventStation`) with a required headcount and individual assignments (`StationAssignment`):

| Action | Method | Route |
|--------|--------|-------|
| Station board | GET | `<event_pk>/postes/` |
| Create station | POST | `<event_pk>/postes/creer/` |
| Delete station | POST | `postes/<pk>/supprimer/` |
| Add person | POST | `postes/<pk>/affecter/` |
| Remove person | POST | `affectations/<pk>/retirer/` |

### Equipment (`equipment/`)

Inventory items (`Equipment`) and loan records (`EquipmentLoan`) managed through an HTMX interface. Loans track borrower, dates, and an optional agreement document. Quantities are computed in real time (`loaned_quantity`, `available_quantity`).

| Action | Method | Route |
|--------|--------|-------|
| Board | GET | `equipment/` |
| Create item | POST | `equipment/creer/` |
| Delete item | POST | `equipment/<pk>/supprimer/` |
| Create loan | POST | `equipment/prets/creer/` |
| Delete loan | POST | `equipment/prets/<pk>/supprimer/` |
| Finalize loan | POST | `equipment/prets/<pk>/finaliser/` |
| Add item to loan | POST | `equipment/prets/<pk>/ajouter/` |
| Remove item | POST | `equipment/prets/lignes/<pk>/retirer/` |

### AI Analysis (`ia/`)

Powered by **Mistral AI**. Requires `MISTRAL_API_KEY`.

- **Summarize** — sends a document through OCR (`mistral-ocr-latest`) then generates a summary (`mistral-small-latest`).
- **Global analysis** — OCRs all documents in a collection and answers a free-form question against their combined content.

| Action | Method | Route |
|--------|--------|-------|
| Summarize document | POST | `ia/documents/<doc_id>/resumer/` |
| Global analysis | POST | `ia/analyser/` |

Results are stored as `Summary` records and displayed inline via HTMX.

### Page hierarchy

```
HomePage
  └── EventIndexPage
        └── EventPage
```

### Front-end

Tailwind CSS 4 is compiled from [`project/static/src/input.css`](project/static/src/input.css) to `project/static/css/output.css`. HTMX is loaded via CDN in [`base.html`](project/templates/base.html).

## Development

```sh
npm run build          # one-off production build (minified)
ruff check .           # lint
ruff format .          # format
python manage.py test  # run all tests
```

## Tests

72 tests cover the `core/` and `events/` apps. Docstrings follow **Gherkin** format (Given / When / Then).

| File | Coverage |
|------|----------|
| [`core/tests.py`](core/tests.py) | `CustomDocument`: `__str__`, default collection, custom collection assignment |
| [`events/tests.py`](events/tests.py) | Page hierarchy · Index rendering & pagination · `PageViewRestriction` access · `can_view_details` flag · Documents by collection · `EventPage` properties · `EventStation` / `StationAssignment` models · Station views (permissions, CRUD, HTMX partials) |

Two shared mixins build the test context: `EventPageTreeMixin` (page tree) and `StationViewMixin` (users: superuser, group moderator, anonymous).

## Production

1. Set `DEBUG=False`, `SECRET_KEY`, `ALLOWED_HOSTS`, and the three `DB_*` variables.
2. Collect static files:
   ```sh
   npm run build
   python manage.py collectstatic
   ```
3. HTTPS and HSTS are enforced automatically when `DEBUG=False`.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit your changes and open a pull request

Please run `ruff check .` and `python manage.py test` before submitting.

## License

[MIT](LICENSE)