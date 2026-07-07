# AutoClub cabinet architecture analysis for Federal Women Club migration

Дата анализа: 2026-05-09.

Scope: source/reference `Kosmos327/autoclub_nsk_web` main branch and target `Kosmos327/fed_women_club_WEB` current branch. Runtime code, migrations, frontend, and backend were not changed in this PR; this is a docs-only migration analysis.

> Note: direct `git clone` from GitHub was blocked in the execution environment with HTTP 403 on the CONNECT tunnel, so source files were inspected via GitHub web/raw endpoints. The target repository was inspected from the local checkout.

## 1. Full AutoClub WEB map

### 1.1 Router composition

AutoClub exposes a flat `api_router = APIRouter()` and mounts endpoint modules with prefixes:

- `/auth` -> `auth.router`
- `/admin` -> `admin.router`
- `/partners` -> `partners.router`
- `/clients` -> `clients.router`
- `/discounts` -> `discounts.router`
- `/leads` -> `leads.router`
- `/vk` -> `vk.router`
- health router is also included.

The architecture is a role-based FastAPI API over SQLAlchemy async sessions, with shared services under `app/services`.

### 1.2 Admin endpoints

AutoClub admin endpoints are protected by `require_role(UserRole.ADMIN)`. The admin cabinet is the operational back office for users, partners, QR links, payment moderation, lead stats, and discount-code audit.

| Method/path | Purpose | Models involved | Schemas/services involved |
| --- | --- | --- | --- |
| `GET /admin/test` | Smoke check for admin access. | `User` | `require_role` |
| `POST /admin/users` | Create user with `admin`/`partner`/`client` role; auto-creates `Client` profile when role is `client`. | `User`, `Client` | `UserCreate`, `UserRead`, `create_user`, `ensure_client_for_user` |
| `GET /admin/users` | List all users ordered by id. | `User` | `UserRead` |
| `GET /admin/partners?is_active=` | List partners, optionally by active status. | `Partner` | `PartnerRead`, `list_partners` |
| `POST /admin/partners` | Create partner and optionally bind `owner_user_id`. | `Partner`, `User` | `PartnerCreate`, `PartnerRead`, `create_partner` |
| `GET /admin/partners/{partner_id}` | Get partner card. | `Partner` | `PartnerRead`, `get_partner` |
| `PATCH /admin/partners/{partner_id}` | Update partner profile, owner, status. | `Partner`, `User` | `PartnerUpdate`, `PartnerRead`, `update_partner` |
| `POST /admin/partners/{partner_id}/locations` | Add partner location. | `PartnerLocation` | `PartnerLocationCreate`, `PartnerLocationRead`, `create_partner_location` |
| `GET /admin/partners/{partner_id}/locations` | List partner locations. | `PartnerLocation` | `PartnerLocationRead`, `list_partner_locations` |
| `POST /admin/partners/{partner_id}/qr-links` | Create QR/referral link; API response enriches it with `qr_url = WEB_PUBLIC_URL + /r/p/{slug}`. | `PartnerQrLink` | `PartnerQrLinkCreate`, `PartnerQrLinkRead`, `create_partner_qr_link` |
| `GET /admin/partners/{partner_id}/qr-links` | List QR links for partner with public QR URL. | `PartnerQrLink` | `PartnerQrLinkRead`, `list_partner_qr_links` |
| `GET /admin/payment-requests?status=` | List payment requests with receipts and client identity. | `PaymentRequest`, `PaymentReceipt`, `Client`, `User` | `PaymentRequestRead` |
| `GET /admin/payment-requests/{payment_request_id}` | Get payment request with receipts/client. | `PaymentRequest` | `PaymentRequestRead` |
| `POST /admin/payment-requests/{payment_request_id}/approve` | Approve paid request and create/extend subscription. | `PaymentRequest`, `Subscription` | `PaymentRequestApproveResponse`, `SubscriptionRead`, `approve_payment_request` |
| `POST /admin/payment-requests/{payment_request_id}/reject` | Reject payment request with optional reason. | `PaymentRequest` | `PaymentRequestRejectRequest`, `PaymentRequestRead`, `reject_payment_request` |
| `GET /admin/leads/partners` | Lead stats grouped by partner QR link. | `LeadClick`, `Partner`, `PartnerQrLink` | `LeadStatsRead`, `get_admin_lead_stats` |
| `GET /admin/discount-codes?status=&partner_id=&client_id=` | Audit/list discount codes with partner/client/service details. | `DiscountCode`, `Partner`, `Client`, `PartnerService` | `DiscountCodeRead`, `serialize_discount_code` |

### 1.3 Partner endpoints

Partner endpoints use `require_role(UserRole.PARTNER)` for own cabinet and `require_role(UserRole.CLIENT, UserRole.ADMIN)` for public catalog reads.

| Method/path | Purpose | Models | Schemas/services |
| --- | --- | --- | --- |
| `GET /partners/test` | Smoke check for partner/admin access. | `User` | `require_role` |
| `GET /partners/catalog` | Active partner catalog visible to clients/admin. | `Partner` | `PartnerRead`, `list_partners` |
| `GET /partners/me` | Partner owner retrieves own partner profile by `owner_user_id == current_user.id`. | `Partner`, `User` | `PartnerRead` |
| `PATCH /partners/me` | Partner edits own public profile fields. | `Partner` | `PartnerProfileUpdate`, `PartnerRead` |
| `POST /partners/me/profile-image` | Upload own logo or cover image; writes to configured uploads directory. | `Partner` | `PartnerRead` |
| `GET /partners/me/locations` | List own locations. | `PartnerLocation` | `PartnerLocationRead`, `list_partner_locations` |
| `GET /partners/me/qr-links` | List own QR links with public QR URL. | `PartnerQrLink` | `PartnerQrLinkRead`, `list_partner_qr_links` |
| `GET /partners/me/services` | List own services/offers. | `PartnerService` | `PartnerServiceRead`, `list_partner_services`, `calculate_final_price` |
| `POST /partners/me/services` | Create own service/discount item. | `PartnerService` | `PartnerServiceCreate`, `PartnerServiceRead`, `create_partner_service` |
| `PATCH /partners/me/services/{service_id}` | Update own service. | `PartnerService` | `PartnerServiceUpdate`, `PartnerServiceRead`, `update_partner_service` |
| `DELETE /partners/me/services/{service_id}` | Soft-deactivate own service. | `PartnerService` | `deactivate_partner_service` |
| `POST /partners/me/services/{service_id}/image` | Upload service image/background. | `PartnerService` | `PartnerServiceRead` |
| `GET /partners/{partner_id}/services` | Public/role-protected active service list. | `PartnerService` | `PartnerServiceRead`, `list_partner_services(active_only=True)` |

### 1.4 Client endpoints

Client endpoints use `get_client_by_user_or_404` to translate authenticated `User` into `Client` profile.

| Method/path | Purpose | Models | Schemas/services |
| --- | --- | --- | --- |
| `GET /clients/test` | Smoke check for client/admin access. | `User` | `require_role` |
| `POST /clients/me/payment-requests` | Client creates payment request for subscription. | `Client`, `PaymentRequest` | `PaymentRequestCreate`, `PaymentRequestRead`, `create_payment_request` |
| `GET /clients/me/payment-requests` | Client lists own payment requests. | `PaymentRequest` | `PaymentRequestRead` |
| `POST /clients/me/payment-requests/{id}/mark-paid` | Client marks own request as paid. | `PaymentRequest` | `PaymentRequestRead`, `mark_payment_paid` |
| `POST /clients/me/payment-requests/{id}/receipts` | Client attaches payment receipt. | `PaymentReceipt` | `PaymentReceiptCreate`, `PaymentReceiptRead`, `add_payment_receipt` |
| `GET /clients/me/subscription` | Client retrieves latest subscription. | `Subscription` | `SubscriptionRead` |
| `GET /clients/me/discount-codes` | Client lists own discount codes. | `DiscountCode` | `DiscountCodeRead`, `list_client_discount_codes`, `serialize_discount_code` |

### 1.5 Auth endpoints and role-based access

Auth uses a single `users` table with role values from `UserRole` (`admin`, `partner`, `client`). The login payload is `{login, password}`, where `login` can be email or phone. `authenticate_user` rejects missing password hashes, inactive users, and invalid credentials. JWT payload contains `user_id` and `role`.

Endpoints:

- `POST /auth/login` -> `TokenResponse`.
- `GET /auth/me` -> `UserRead` for current user.

Access is enforced with dependencies:

- `get_current_user`: parses bearer token and loads `User`.
- `require_role(...)`: allows only specified roles.
- `require_bot_api_token`: used by VK endpoints instead of user JWT.

### 1.6 Discounts, QR, leads, payments, VK

#### Discounts

AutoClub has a two-step WEB discount-code flow:

1. `POST /discounts/intents`: client creates short-lived `DiscountCodeIntent` for partner/service.
2. `POST /discounts/intents/{intent_id}/confirm`: client confirms intent and receives an active code.
3. `GET /discounts/codes/{code}`: partner/admin checks code validity.
4. `POST /discounts/codes/{code}/redeem`: partner/admin redeems active code.

Rules in `discount_service`:

- intent TTL: 10 minutes;
- WEB code TTL: 15 minutes;
- daily client code limit: 5;
- monthly one-code-per-client-per-partner guard;
- partner user can check/redeem only codes belonging to their partner profile;
- active/used/expired/revoked effective status handling.

#### QR links and lead tracking

AutoClub stores partner QR links as `PartnerQrLink(slug, target_url, is_active)`. Admin and partner list endpoints build public URLs as `WEB_PUBLIC_URL/r/p/{slug}`. The lead service records `LeadClick` with hashed IP/user-agent, `session_id`, UTM fields, and referer. It deduplicates clicks per QR link + effective session. Lead stats are aggregated by partner and QR link for admin and by owner user for partner.

VK verify sessions also record a synthetic lead with `session_id = vk:{vk_user_id}`, `utm_source = vk_bot`, `utm_campaign = verify_partner`.

#### Payments and subscriptions

Payment workflow:

1. Client or VK creates a `PaymentRequest` with amount.
2. Client/VK marks it as paid and can attach a receipt.
3. Admin approves only `PAID` requests and requires at least one receipt.
4. Approval creates a new 30-day active subscription or extends an existing active subscription by 30 days.
5. Admin can reject non-approved requests with reason and audit fields.

Core statuses:

- `PaymentRequestStatus`: `new`, `paid`, `approved`, `rejected`.
- `ReceiptUploadSource`: `vk`, `web`.
- `SubscriptionStatus`: `active`, `expired`, `paused`.

#### VK endpoints

VK routes are protected by bot service token and expose bot-facing contracts:

- `POST /vk/auth`: get/create VK client profile and associated `User(role=client)`.
- `GET /vk/subscription`: return active/latest subscription state.
- `GET /vk/catalog/categories`: category list with partner counts.
- `GET /vk/catalog/partners`: paginated active partners with service previews.
- `GET /vk/partners/{partner_id}`: partner detail with locations/services.
- `GET /vk/partners/{partner_id}/services`: active services for partner.
- `POST /vk/discount-codes/request`: active subscription required; creates code valid until subscription ends.
- `POST /vk/verify-partner`: active subscription required for dynamic verification code; returns no-subscription response otherwise.
- `GET /vk/my-codes`: list client codes by VK id.
- `POST /vk/payment-request`: get/create current payment request.
- `POST /vk/payment-request/mark-paid`: mark request paid.
- `POST /vk/payment-request/receipt`: attach VK receipt and mark paid if needed.
- `GET /vk/payment-request/latest`: latest payment request for VK user.

### 1.7 AutoClub models

| File | Models/enums | Notes |
| --- | --- | --- |
| `app/models/user.py` | `User` | Single user table with `role`, `email`, `phone`, `password_hash`, `is_active`; relationships to `client_profile` and `owned_partners`. |
| `app/models/client.py` | `Client` | One-to-one `user_id`, optional `full_name`, `vk_user_id`, referral fields; related payment/subscription/code/verify records. |
| `app/models/partner.py` | `Partner`, `PartnerLocation`, `PartnerQrLink`, `PartnerService` | Partner has optional `owner_user_id`, category, contacts, images, active flag. QR links and services are partner-owned. |
| `app/models/payment.py` | `PaymentRequest`, `PaymentReceipt`, `Subscription`, `PaymentRequestStatus`, `ReceiptUploadSource`, `SubscriptionStatus` | Subscription is tied to client, not city. Payment request stores audit and `access_until`. |
| `app/models/discount.py` | `DiscountCodeIntent`, `DiscountCode`, status enums | Code lifecycle and service-specific partner privilege use. |
| `app/models/lead.py` | `LeadClick` | QR click tracking with dedupe identifiers and UTM/referrer fields. |
| `app/models/verify.py` | `PartnerVerifySession`, `PartnerVerifySessionStatus` | Dynamic short verification code for partner privilege confirmation. |

### 1.8 AutoClub schemas

| File | Schemas |
| --- | --- |
| `app/schemas/auth.py` | `LoginRequest`, `TokenResponse`, `TokenPayload` |
| `app/schemas/user.py` | `UserRead`, `UserCreate` |
| `app/schemas/partner.py` | `PartnerCreate`, `PartnerUpdate`, `PartnerProfileUpdate`, `PartnerRead`, `PartnerLocationCreate/Read`, `PartnerQrLinkCreate/Read`, `PartnerServiceCreate/Update/Read` |
| `app/schemas/payment.py` | `PaymentRequestCreate/Read`, `PaymentReceiptCreate/Read`, `PaymentRequestApproveResponse`, `PaymentRequestRejectRequest` |
| `app/schemas/subscription.py` | `SubscriptionRead` |
| `app/schemas/discount.py` | `DiscountIntentCreate/Read`, `DiscountCodeRead`, `DiscountCodeCheckResponse`, `DiscountCodeRedeemResponse` |
| `app/schemas/lead.py` | `LeadClickRead`, `LeadStatsRead` |
| `app/schemas/vk.py` | VK auth, subscription, catalog, partner detail/services, discount code, payment, and verify request/response schemas |

### 1.9 AutoClub services

| File | Responsibilities |
| --- | --- |
| `auth_service.py` | Email/phone login, password verification, role-aware user creation, uniqueness checks. |
| `user_service.py` | `Client` profile lookup/creation for `User`. |
| `partner_service.py` | Partner CRUD, owner validation, locations, QR slug generation, QR links, services/offers, final price calculation, soft-delete services. |
| `payment_service.py` | Client WEB payment requests, receipts, mark paid, approval/rejection, 30-day subscription creation/extension. |
| `discount_service.py` | Discount intents, code generation, code TTL/limits, partner-only check/redeem, serialization. |
| `lead_service.py` | QR click hash/dedupe, admin/partner lead stats, VK verify lead recording. |
| `vk_catalog_service.py` | Client-facing category normalization and category membership. |
| `vk_discount_service.py` | VK subscription-gated code generation and client code listing. |
| `vk_payment_service.py` | VK payment request idempotency, mark paid, receipt attach, latest request. |
| `vk_verify_service.py` | VK client get/create, active subscription lookup, dynamic verification code generation, verify session creation, verify-lead tracking. |

### 1.10 AutoClub migrations

AutoClub migration chain contains 11 staged migrations:

1. `20260428_0001_init_skeleton.py`
2. `20260428_0002_payment_and_subscription.py`
3. `20260428_0003_partner_locations_and_qr_links.py`
4. `20260428_0004_lead_clicks.py`
5. `20260428_0005_discount_codes_mvp.py`
6. `20260430_0006_unique_lead_visitors.py`
7. `20260430_0007_payment_requests_admin_audit_fields.py`
8. `20260430_0008_partner_services.py`
9. `20260501_0009_discount_code_partner_service.py`
10. `20260501_0010_partner_profile_fields.py`
11. `20260508_0011_partner_verify_sessions.py`

This is already a good template for small migration PRs in Women Club, but the exact DDL should not be copied blindly because target currently has a different partial skeleton and a separate admin auth table.

### 1.11 AutoClub frontend cabinet logic

AutoClub frontend is a Vite React/TypeScript SPA. Its `App.tsx` has:

- token storage in `localStorage` under `access_token`;
- `apiFetch` wrapper adding bearer token;
- `/login` page calling `/api/v1/auth/login` then `/api/v1/auth/me`;
- role guard redirecting users by `admin`/`client`/`partner`;
- separate navs and layouts for admin, client, partner;
- admin pages for dashboard, users, partners, payments, leads, discount codes, code check;
- partner pages for profile, services, code check/redeem, leads;
- client pages for subscription, partners, own codes, code request.

For Women Club, this frontend is conceptually reusable but not directly copy-paste compatible because target frontend is plain JavaScript with static markup, not React Router/TSX.

## 2. Comparison with fed_women_club_WEB

### 2.1 What already exists in target

Current target is a lightweight MVP skeleton with a small amount of real admin auth:

- API router has `/api/v1` prefix and currently includes only `auth` and `admin` routers.
- `POST /api/v1/auth/login` authenticates against `AdminUser` by email/password and returns a bearer token plus `AdminUserRead`.
- `GET /api/v1/admin/me` returns current admin via `require_admin`.
- `app/api/deps.py` supports only admin bearer-token dependencies and enforces `AdminUser.role == admin`.
- `AdminUser` is the only SQLAlchemy runtime model; most other domain models (`City`, `Partner`, `ClientProfile`, `DiscountCode`, `LeadClick`, `PaymentRequest`, `VerificationRequest`) are dataclass skeletons, not persisted ORM models.
- Target has a multi-city dataclass/migration skeleton and women-club categories.
- Frontend is plain JS/CSS: public landing page, city chips for Новосибирск and Череповец, category cards, and a minimal admin login/dashboard calling `/api/v1/auth/login` and `/api/v1/admin/me`.
- Tests cover health, config, migrations, admin auth, city/category skeletons, create-admin script, and frontend content.

### 2.2 What is missing for cabinet architecture

Target is missing most AutoClub cabinet architecture:

- no unified `users` table for admin/partner/client roles;
- no persisted `clients`, `partners`, partner owner link, locations, QR links, services/offers, payment requests, receipts, subscriptions, discount/verify sessions, lead clicks;
- no partner/client auth or role dependencies;
- no admin endpoints for users, cities/categories, partners, QR, payments, leads, discount/verification audit;
- no partner cabinet endpoints;
- no client cabinet endpoints;
- no VK bot endpoint group;
- no persisted services for payments/subscriptions/verify sessions;
- no frontend cabinet routing beyond minimal admin login block.

### 2.3 What can be ported almost directly

These parts are good candidates for adapted direct transfer:

- role names `admin`, `partner`, `client` and high-level dependency shape;
- partner owner pattern `Partner.owner_user_id -> User.id` with validation that owner has `partner` role;
- `Client` profile one-to-one with `User`;
- payment request + receipt + global subscription workflow;
- lead tracking dedupe logic using hashed request traits and `session_id`;
- QR link concept with `slug` and generated public URL;
- partner services CRUD, renamed to offers/privileges;
- verify session model and VK `verify-partner` API concept;
- staged migration sequencing.

### 2.4 What must be adapted for multi-city and Women Club domain

Required adaptations:

- Add a persisted `City` ORM model and use active seed cities only: Новосибирск and Череповец for MVP.
- Add `city_id` to partners and partner locations/offers where needed; partner catalog and VK catalog must filter by city.
- Keep subscription global, not city-scoped. A client with active subscription can use privileges in any active MVP city.
- Replace AutoClub auto categories with women-club categories (`Красота`, `Маникюр / педикюр`, etc.).
- Rename user-facing `PartnerService` language to offer/privilege while preserving backend simplicity; e.g. table can be `partner_offers` or `partner_privileges` rather than service if introducing new DDL.
- Replace AutoClub discount-code UX with privilege confirmation / verify sessions as primary flow.
- Use QR / VK deep links shaped around `verify_partner_<partner_id>` for bot entry, while WEB QR slugs can still exist for lead tracking and redirect/verification starts.
- Ensure city filtering is explicit in admin and catalog endpoints (`city_id`/`city_slug`), not hard-coded NSK.

### 2.5 What should not be ported directly

Do not copy these directly without design adjustment:

- AutoClub `users` auth code over target as-is: target currently uses `AdminUser` and sync SQLAlchemy sessions, while AutoClub uses async sessions and a unified `User` table.
- AutoClub frontend `App.tsx` as-is: target frontend is vanilla JS/CSS and tests assert exact strings/static structure.
- AutoClub auto category normalization: categories are domain-specific.
- AutoClub pricing/discount percent labels as the only privilege representation: Women Club privileges may be gifts, confirmations, perks, or access statuses, not only numeric discounts.
- AutoClub VK code prefix `AC`, referral `AC{vk_user_id}`, and public copy.
- Any migration copied verbatim over target's existing Alembic chain; target has its own heads and skeleton migration history.

## 3. Specific AutoClub mechanisms to preserve/adapt

### 3.1 `partner.owner_user_id`

AutoClub stores optional `owner_user_id` on `Partner`. Admin can set/update it. Partner cabinet resolves the current partner by querying `Partner.owner_user_id == current_user.id`; if no partner is bound, endpoints return 404. Owner validation rejects non-existing users and users whose role is not `partner`.

Women Club recommendation: keep the same pattern, but ensure uniqueness if MVP expects one partner account to own one partner. If multiple branches/locations under one brand need several partner accounts later, add an explicit ownership/link table later, not in MVP.

### 3.2 Client profile

AutoClub has `Client(user_id unique, full_name, vk_user_id unique, referral_code unique, referrer_client_id)`. Admin-created client users receive a profile through `ensure_client_for_user`. VK auth can create a client user/profile without email/password.

Women Club recommendation: keep `ClientProfile` one-to-one with `User`, add `selected_city_id` for UX preferences only, not subscription entitlement.

### 3.3 Payment request

AutoClub `PaymentRequest` belongs to `Client`, has amount, status, audit fields, receipts, `access_until`, and `is_renewal`. Approval requires paid status and a receipt, then creates or extends a subscription.

Women Club recommendation: use the same global subscription payment flow; amount should come from settings/admin plan configuration, not city. Keep VK and WEB receipt attachment separate from payment provider integrations.

### 3.4 Subscription

AutoClub subscription belongs to client, with `status`, `starts_at`, `ends_at`, and source payment request. It is global and independent from partner/city.

Women Club recommendation: keep subscription global in MVP; city only filters partner availability/catalog, not access entitlement.

### 3.5 Discount code

AutoClub discount code is a short code tied to client, partner, optional partner service, status, expiry, and `used_by_user_id`. WEB code TTL is short; VK code lasts until subscription end.

Women Club recommendation: migrate the integrity/audit ideas, not the primary UX. Prefer `PrivilegeVerificationSession` with dynamic code, QR/VK session source, status, expiry, and partner/client bindings. Keep legacy discount-code endpoints only if required for interim compatibility.

### 3.6 QR link

AutoClub QR link is a partner-owned slug with optional target URL and active flag. Public URL is generated from `WEB_PUBLIC_URL/r/p/{slug}`. Leads are attached to QR link.

Women Club recommendation: keep partner QR link for lead attribution, but target the user journey to VK deep link `verify_partner_<partner_id>` or WEB verification start. Store `partner_id`, `city_id` context if useful, `slug`, `deep_link_payload`, `target_url`, `is_active`.

### 3.7 Lead stats

AutoClub lead stats aggregate `LeadClick` counts by partner and QR link. Partner stats are scoped by `owner_user_id`. Lead recording deduplicates by QR link and session/fingerprint.

Women Club recommendation: same concept, add dimensions for city and source (`web_qr`, `vk_verify`, `catalog`, etc.) only if needed in small increments.

### 3.8 Role-based access

AutoClub centralizes roles in `UserRole` and uses `require_role(...)` in every cabinet endpoint. VK endpoints use bot-token auth, not user JWT.

Women Club recommendation: move toward unified `User`/role auth carefully. In early PRs, keep existing admin auth stable or bridge `AdminUser` to `User` after a migration plan. Do not mix partner/client auth rollout with VK bot endpoints.

## 4. Adaptation mappings

### 4.1 AutoClub discount codes -> Women Club privilege confirmations / verify sessions

Map AutoClub objects as follows:

- `DiscountCodeIntent` -> optional `PrivilegeIntent` or skip in MVP if QR/VK immediately creates verification session.
- `DiscountCode` -> `PrivilegeVerificationSession` with dynamic code, source, status, and expiry.
- `check_discount_code` -> partner endpoint `check_verify_session` or `verify_dynamic_code`.
- `redeem_discount_code` -> partner endpoint `confirm_privilege_use` / `complete_verify_session`.
- `DiscountCodeStatus.active/used/expired/revoked` -> `VerifySessionStatus.active/confirmed/expired/cancelled`.
- `partner_service_id` -> `offer_id` / `privilege_id`, optional if partner-level privilege is enough.

The key adaptation is that Women Club should confirm membership/privilege eligibility, not present the user experience as coupon-code discount redemption only.

### 4.2 AutoClub partner services -> Women Club offers / privileges

Map `PartnerService` to `PartnerOffer` or `PartnerPrivilege`:

- `title`, `description`, `image_url`, `background_url`, `is_active`, `sort_order` can transfer.
- `base_price` and `discount_percent` should become optional; do not force every privilege to be a percent discount.
- Add `privilege_type` only if needed (`discount`, `gift`, `bonus`, `special_offer`) but avoid over-modeling in PR 1.
- Keep `discount_text` as human-readable `benefit_text` / `privilege_text`.

### 4.3 AutoClub city/NSK logic -> multi-city Новосибирск/Череповец

AutoClub has one-city assumptions in brand/copy and does not have a persisted city model in the inspected source. Women Club target already introduces a `City` concept. Migration plan should:

- seed only `novosibirsk` and `cherepovets` for MVP;
- attach `Partner.city_id` and optionally `PartnerLocation.city_id`;
- filter public/client/VK partner catalogs by `city_id`/`city_slug`;
- keep subscription global;
- keep admin city/category management separate from partner CRUD PRs;
- ensure partner counts/categories are city-aware in VK catalog.

## 5. Staged roadmap as small PRs

### PR 1: foundation models/migrations

- Goal: establish persistent core domain without endpoints changing runtime behavior broadly.
- Files to change: `app/models/user.py`, new/updated ORM files under `app/models/`, `app/db/base.py`, `app/schemas/user.py`, `app/schemas/city.py`, Alembic versions, tests under `tests/`.
- Endpoints to add: none or only no-op imports; keep public API stable.
- Tests to add: migration head tests, model instantiation/DB persistence tests, role enum tests, city seed tests.
- Risks: conflict with existing `AdminUser`; async vs sync DB choice; migration chain mistakes.
- Do not touch: frontend cabinet UI, VK endpoints, payment logic.

### PR 2: admin cities/categories

- Goal: admin CRUD/list for MVP cities and Women Club categories.
- Files to change: `app/api/v1/router.py`, `app/api/v1/endpoints/admin.py` or separate admin city/category modules, `app/models/city.py`, `app/core/categories.py`, schemas/tests.
- Endpoints to add: `GET/POST/PATCH /api/v1/admin/cities`, `GET /api/v1/admin/categories`.
- Tests to add: admin auth required, list seed cities, create/update city validation, categories list.
- Risks: frontend currently hardcodes cities; DB cities may diverge from UI.
- Do not touch: partner/client cabinet endpoints, VK bot.

### PR 3: admin partners

- Goal: admin can create/list/update city-scoped partners and bind partner owner.
- Files to change: partner ORM/schemas/services, `app/api/v1/endpoints/admin.py`, tests.
- Endpoints to add: `GET/POST /api/v1/admin/partners`, `GET/PATCH /api/v1/admin/partners/{id}`.
- Tests to add: create partner in Новосибирск/Череповец, owner role validation, city filter, active filter.
- Risks: deciding whether to migrate from `AdminUser` to unified `User` now or use interim admin-only owner references.
- Do not touch: partner self-service, payments, QR, frontend heavy UI.

### PR 4: partner cabinet backend

- Goal: partner role can manage own profile after owner binding exists.
- Files to change: auth/deps for partner role, partner endpoints/services/schemas, tests.
- Endpoints to add: `GET/PATCH /api/v1/partners/me`, `GET /api/v1/partners/me/locations` if locations are already in schema.
- Tests to add: partner can access only own profile, admin cannot accidentally mutate as partner unless intended, unbound partner gets 404.
- Risks: auth migration from admin-only JWT to multi-role JWT.
- Do not touch: client cabinet, payments, VK bot, frontend.

### PR 5: client cabinet backend

- Goal: client profile and subscription read surface for WEB client cabinet.
- Files to change: client models/schemas/services/endpoints, auth/deps tests.
- Endpoints to add: `GET /api/v1/clients/me`, `PATCH /api/v1/clients/me`, `GET /api/v1/clients/me/subscription`.
- Tests to add: client profile auto-creation, selected_city_id update, subscription absent/present responses.
- Risks: registration/auth scope creep.
- Do not touch: partner offers, QR, VK bot.

### PR 6: offers/services

- Goal: implement Women Club partner offers/privileges using AutoClub service pattern.
- Files to change: offer model/schemas/services, partner/admin endpoints, migrations, tests.
- Endpoints to add: admin offer management under `/admin/partners/{id}/offers`; partner self-service `/partners/me/offers`; public/client `GET /partners/{id}/offers`.
- Tests to add: active-only public list, partner ownership, sort order, optional price/discount fields, city-scoped partner catalog.
- Risks: naming mismatch (`services` vs `offers`) and over-modeling privilege types.
- Do not touch: discount/verify flows, VK bot.

### PR 7: QR/lead tracking

- Goal: partner QR links and lead attribution.
- Files to change: QR/lead models/schemas/services, admin/partner endpoints, redirect endpoint if needed, tests.
- Endpoints to add: `POST/GET /admin/partners/{id}/qr-links`, `GET /partners/me/qr-links`, `GET /leads/me`, `GET /admin/leads/partners`, optional public `GET /r/p/{slug}`.
- Tests to add: unique slug, generated URL, dedupe lead click, admin/partner lead stats, city dimensions if added.
- Risks: redirect/lead endpoint can become frontend/VK integration too early.
- Do not touch: VK bot verify endpoints in this PR.

### PR 8: verify sessions

- Goal: replace coupon-code centric flow with Women Club privilege verification sessions.
- Files to change: verify model/schemas/services/endpoints, tests.
- Endpoints to add: partner `GET/POST /api/v1/verify-sessions/{code}/check|confirm` or equivalent; client `POST /api/v1/clients/me/verify-sessions`; admin audit list.
- Tests to add: active subscription required, session TTL, dynamic code uniqueness, partner ownership, no-subscription response, expired/confirmed statuses.
- Risks: accidentally reintroducing discount-code UI; concurrency around code confirmation.
- Do not touch: VK bot endpoints; expose WEB-only verify first.

### PR 9: frontend admin cabinet

- Goal: expand current vanilla JS admin dashboard to manage cities/categories/partners progressively.
- Files to change: `frontend/src/main.js`, `frontend/src/styles.css`, frontend tests.
- Endpoints consumed: existing admin auth, cities/categories, partners.
- Tests to add: rendered admin navigation/cards/forms, login token behavior, city/category strings, partner CRUD fetch calls if testable.
- Risks: large vanilla JS file becoming hard to maintain; tests assert exact public copy.
- Do not touch: backend migrations, partner/client UI, VK bot.

### PR 10: frontend partner/client cabinet

- Goal: add visible partner/client cabinet screens after backend endpoints are stable.
- Files to change: `frontend/src/main.js`, `frontend/src/styles.css`, frontend tests.
- Endpoints consumed: partner profile/offers/QR/leads; client profile/subscription/catalog/verify.
- Tests to add: role-based screen selection, partner forms, client city selector with active cities, subscription state, no heavy dependencies.
- Risks: target frontend is not React; avoid wholesale copying AutoClub TSX.
- Do not touch: VK bot endpoints.

### PR 11: VK bot integration endpoints

- Goal: bot-token protected Women Club API for VK auth, catalog, global subscription, `verify_partner_<partner_id>`.
- Files to change: `app/api/v1/endpoints/vk.py`, `app/services/vk_*`, schemas, tests.
- Endpoints to add: `/api/v1/vk/auth`, `/api/v1/vk/subscription`, `/api/v1/vk/catalog/categories`, `/api/v1/vk/catalog/partners?city_slug=`, `/api/v1/vk/partners/{id}`, `/api/v1/vk/verify-partner`, payment endpoints only if not already implemented.
- Tests to add: bot token required, city-filtered catalog, active subscription verify success, no-subscription verify response, deep-link payload parser `verify_partner_<partner_id>`.
- Risks: mixing bot and WEB flows; leaking user JWT expectations into bot API.
- Do not touch: WEB frontend in this PR.

## 6. Implementation guardrails

- Do not rewrite the project from scratch; port AutoClub architecture in small slices.
- Do not mix WEB frontend/backend cabinet changes with VK bot integration in one PR.
- Avoid heavy dependencies; target already has stdlib fallbacks for JWT/password hashing.
- Preserve Python 3.10 compatibility (`X | Y` syntax is fine; avoid 3.11-only features).
- Keep subscription global for MVP.
- Keep city filtering explicit and test both MVP cities.
- Prefer docs/API tests and migration tests at each step before UI work.
