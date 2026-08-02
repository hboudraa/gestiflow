# GestiFlow — Project Analysis

> Prepared for an AI reviewer (Claude) to further analyze this Django codebase.
> Working directory: `C:\Users\PC\gestiflow`

## Overview

GestiFlow is a Django business-management (ERP/POS) web application, in French,
localized for Algeria (timezone `Africa/Algiers`, currency DA, TVA 19% default).

- Language: Python (Django), templates (Bootstrap 5 + crispy-forms)
- ~4,400 lines of Python across `apps/`
- 69 HTML templates under `templates/`
- DB: SQLite (dev) / PostgreSQL (prod)
- PDF reports via ReportLab, import/export via django-import-export
- No tests exist (`**/tests.py` returns nothing)
- Git: 2 commits (`b31680d`, `da6e5eb`), both "gestiflow"

## Architecture

Modular apps under `apps/`, mounted in `config/urls.py`:

| App | Purpose | Key models |
| --- | --- | --- |
| `core` | Shared infra | `TimestampedModel`, `SoftDeleteModel`, `Adresse`, `Parametre`, `LogActivite`, notifications, security middleware |
| `authentication` | Auth | `Utilisateur` (AbstractUser + roles), `LoginAttempt` (brute-force lockout) |
| `dashboard` | Home KPI view | — |
| `clients` | CRM | `Client` (credit limit, soft-delete, auto code `CLT00001`) |
| `fournisseurs` | Suppliers | `Fournisseur` |
| `produits` | Catalog/stock | `Categorie`, `Produit`, `MouvementStock`, `HistoriquePrix` |
| `ventes` | Sales | `Facture`, `LigneFacture`, `Paiement` |
| `devis` | Quotes | `Devis`, `LigneDevis` (convertible to Facture) |
| `achats` | Purchases | `AchatFournisseur`, `LigneAchat` |
| `locations` | Rentals | `Location`, `ArticleLocation` |
| `services` | Work orders | `OrdreDeTravail`, `PieceService`, `OutilService`, `FichierService` |
| `comptabilite` | Accounting | `Transaction`, `CategorieDepense` |
| `rapports` | Reports | `pdf_generator.py` (ReportLab) |

## Domain model notes

- Shared mixins in `apps/core/models.py`:
  - `TimestampedModel` — `cree_le`, `modifie_le`
  - `SoftDeleteModel` + `SoftDeleteManager` — `supprime` flag, `all_objects` for full access
  - `Adresse` — abstract address mixin (ligne1, ville, wilaya, code_postal)
- Document numbering auto-generated in `save()` by string-slicing the last
  number: `FAC{year}{seq:05d}`, `DEV`, `ACH`, `LOC`, `OT`, `CLT`, `PRD`.
- `Facture.calculer_totaux()` and `mettre_a_jour_statut()` are called from views.
- `Produit` has `prix_vente_ttc`, `marge_brute`, `en_alerte` properties.

## Configuration

- `config/settings/base.py` — env-driven via `django-environ`, `SECRET_KEY` from env.
  Hardcoded `ALLOWED_HOSTS` entries incl. LAN IPs (`192.168.0.165/196`).
  Custom user `authentication.Utilisateur`, LOGIN_URL `/auth/connexion/`.
  Session 30 min, HTTPOnly, SameSite=Strict. Custom middleware
  `apps.core.security_middleware.SecurityHeadersMiddleware`.
  Static via whitenoise `CompressedManifestStaticFilesStorage`.
- `config/settings/development.py` — SQLite.
- `config/settings/production.py` — PostgreSQL, DEBUG=False, HSTS, SSL redirect,
  secure cookies.
- `config/urls.py` — custom 404/500/403 handlers in `apps/core/views.py`.

## Known issues / review points

1. **Swallowed exceptions**: `try/except Exception: pass` throughout views
   (e.g. `apps/dashboard/views.py:11-37`, `apps/core/views.py:25-62`). Real
   errors are hidden; `print()` is used instead of the logging framework; no
   `LOGGING` dict in settings.
2. **Lazy imports**: models are imported inside functions to avoid circular
   imports instead of top-level imports.
3. **`save()` side-effects**: `calculer_totaux()` calls `self.save()` internally
   (`apps/ventes/models.py:62`, `apps/services/models.py:64`), causing
   double-saves and implicit DB writes from read paths.
4. **Hardcoded TVA**: `apps/locations/models.py:48` hardcodes `Decimal('1.19')`
   instead of using product/settings TVA.
5. **No tests** at all.
6. **Query efficiency**: dashboard month filters
   (`date_facture__month`, `dashboard/views.py:12-13`) can't use the date index.
7. **Dev static storage**: whitenoise manifest storage typically requires
   `collectstatic` even in dev.
8. **Numbering via string slice** (`last.numero[7:]`) is brittle (breaks if
   year/prefix length ever changes).
9. **Untracked clutter**: `.pyc` dirs, `.idea/`, `.ollamassist/` untracked; no
   `.gitignore`.
10. **`Factor` aggregation**: `F('quantite_stock') * F('prix_achat')` in
    `dashboard/views.py:26` requires `DecimalField` compatibility (works).

## Suggested next steps for the reviewer

- Run Django checks: `python manage.py check`
- Run migrations status: `python manage.py showmigrations`
- Verify each app's `admin.py`, `forms.py`, `views.py`, `urls.py` wiring
- Assess data model consistency (FK protection, cascade rules)
- Check `apps/rapports/pdf_generator.py` for layout/security issues
- Look for uncommitted secrets in `.env` / settings
- Propose a test strategy (factories + pytest or Django TestCase)
