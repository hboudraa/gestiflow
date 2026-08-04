# Security fixes applied — Notes for Claude

Date: 2026-08-03

This file documents the recent security-focused changes made to the GestiFlow codebase and explains why they were applied. Use this as a short handoff for follow-up reviews or CI checks.

## Summary of changes
I applied five targeted security hardening edits requested by the reviewer:

1. Prevent open-redirect on login `next` parameter
   - File: apps/authentication/views.py
   - Change: Validate the `next` parameter using `django.utils.http.url_has_allowed_host_and_scheme` before calling `redirect()`; otherwise fall back to the safe landing page.
   - Why: Prevents open-redirect attacks that could be used in phishing flows or to leak tokens.

2. Escape email body content before embedding in HTML
   - File: apps/core/email_service.py
   - Change: Use `django.utils.html.escape` on the `corps` value before converting newlines to `<br>` and embedding into the email HTML.
   - Why: Prevents HTML/JS injection into generated HTML emails.

3. Simple uploaded Excel type check on import
   - File: apps/produits/views.py
   - Change: Validate the uploaded filename extension (allowed: `.xlsx`, `.xlsm`, `.xltx`, `.xls`) before calling `openpyxl.load_workbook`.
   - Why: Prevents some classes of processing of unexpected file types. (Size checking, MIME-type and content validation can be added later.)

4. Safer handling of X-Forwarded-For for IP-based throttling
   - File: apps/authentication/models.py
   - Change: `LoginAttempt.get_ip()` now checks `settings.USE_X_FORWARDED_FOR` before trusting `HTTP_X_FORWARDED_FOR`. If the setting is not True, `REMOTE_ADDR` is used instead.
   - Why: Avoids IP spoofing unless deployment explicitly enables trusting the proxy header.

5. Add a basic Content-Security-Policy header
   - File: apps/core/security_middleware.py
   - Change: Add a conservative `Content-Security-Policy` header and handle header removal robustly.
   - Why: Reduces XSS attack surface by restricting resource origins. This CSP is conservative and should be reviewed against production asset/CDN needs.

## Files changed
- [apps/authentication/views.py](C:/Users/AnieLaptop/PycharmProjects/gestiflow/apps/authentication/views.py)
- [apps/authentication/models.py](C:/Users/AnieLaptop/PycharmProjects/gestiflow/apps/authentication/models.py)
- [apps/core/email_service.py](C:/Users/AnieLaptop/PycharmProjects/gestiflow/apps/core/email_service.py)
- [apps/core/security_middleware.py](C:/Users/AnieLaptop/PycharmProjects/gestiflow/apps/core/security_middleware.py)
- [apps/produits/views.py](C:/Users/AnieLaptop/PycharmProjects/gestiflow/apps/produits/views.py)

(See the diffs in the working tree for exact edits.)

## Testing done
- Ran the repository's existing pytest tests (apps/ventes/tests.py and apps/locations/tests.py) — they passed prior to these edits and there were no failing tests after the edits.
- Manual code inspection and grep-based scanning to confirm no obvious regressions from these edits.

## Recommendations / Next steps
1. Enable `USE_X_FORWARDED_FOR = True` in production settings only if the app is behind a trusted proxy (and document which proxies are trusted). See `config/settings/production.py`.
2. Replace the filename-only Excel check with additional checks:
   - Validate MIME type (if available), open a small sample of the workbook and check worksheets/cell counts before processing, and/or enforce a MAX file size.
3. Add unit tests for:
   - Open-redirect protection: requests with safe and unsafe `next` values.
   - Email escaping: ensure HTML in `corps` is escaped.
   - Excel import: rejected extension paths.
4. Review CSP header in `apps/core/security_middleware.py` and adapt to any external CDNs or third-party scripts used in production.
5. Replace broad `except Exception` blocks in the codebase with narrower exception handling and ensure important errors are propagated to logs/alerts.

## Commands to run locally
- Install deps: `python -m pip install -r requirements.txt`
- Run checks (development):
  - `set SECRET_KEY=dummysecret` (Windows PowerShell: `$env:SECRET_KEY='dummysecret'`)
  - `python manage.py check --settings=config.settings.development`
  - `python -m pytest -q`

## Contact
If additional context is needed, please review the commit(s) in the working directory or ask here for a specific diff/patch.

-- Automated note: file created by the Copilot/CLI assistant during a code review session.
