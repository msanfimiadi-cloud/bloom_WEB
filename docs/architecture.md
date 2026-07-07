# Architecture

Federal Women Club WEB starts from an imported MVP web/backend skeleton for a subscription club platform.

The skeleton keeps separate backend, frontend, tests, scripts, and Alembic migration areas so city-specific behavior can be introduced without turning the project into a single-city deployment.

## Multi-city baseline

The product is federal by design. City is a first-class dictionary entity used by
partner catalog filtering, admin filters, analytics filters, and client city
selection. The MVP deliberately keeps subscription global for the whole club.

One partner belongs to one city in the MVP. Branches/locations are intentionally
out of scope until the business model requires them.

The current codebase is still a lightweight dataclass/routing placeholder rather
than a full persistence-backed FastAPI implementation, so multi-city behavior is
introduced as models, migration skeleton, docs, and service-level filter helpers.
