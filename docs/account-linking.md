# Bloom Club account linking ADR

Status: **proposed foundation**  
Date: **2026-06-06**  
Scope: backend account architecture for the Bloom Club site, VK Mini App, and Telegram Mini App.

## Context

Bloom Club currently has three entry points that can create or reuse client accounts:

- Site login: `POST /auth/user-login` authenticates an existing `User` by email, phone, or `site_login` and returns a unified user token.
- VK Mini App login: `POST /auth/vk-miniapp-login` verifies VK launch parameters, then looks up `ClientProfile` by `vk_user_id` only. If no profile exists, it creates a new `User` and a new `ClientProfile` with `source="vk-miniapp"`.
- Telegram Mini App login: `POST /auth/telegram-miniapp-login` verifies Telegram `init_data`, then looks up `ClientProfile` by `telegram_user_id` only. If no profile exists, it creates a new `User` and a new `ClientProfile` with `source="telegram-miniapp"`.
- Client profile update: `PATCH /clients/me` can update `User.phone`, `User.email`, and `ClientProfile.contact_email`, but this data is not treated as verified identity proof for VK/Telegram login.
- Trial subscription activation: `POST /clients/me/trial-subscription` checks and writes `ClientProfile.trial_subscription_used_at`, so trial usage is currently scoped to a single `ClientProfile`.

This means the same real person can be represented by multiple `User` + `ClientProfile` rows when they enter from different platforms before a safe linking flow exists. The most important product risk is repeated trial eligibility across duplicated profiles.

## Decision

Bloom Club will move toward this account model:

1. **One real client should map to one `User` and one `ClientProfile`.**
   - `User` remains the authentication/account owner.
   - `ClientProfile` remains the client-domain profile and subscription owner.
2. **External platform identities are explicit identity links.**
   - VK identity: provider `vk`, `provider_user_id=<vk_user_id>`.
   - Telegram identity: provider `telegram`, `provider_user_id=<telegram_user_id>`.
   - Site identity: provider `site`, `provider_user_id=<site_login|user_id>` when needed for a normalized identity registry.
3. **Phone and email must be verified before they can be used for account linking.**
   - `phone_verified_at` and `email_verified_at` are nullable timestamps on `users`.
   - A non-null timestamp means that the current user has proven control of that phone/email through an approved verification flow.
   - Unverified phone/email values are profile/contact data only and must not trigger automatic merging.
4. **Trial eligibility must eventually be evaluated by verified identity/link group, not just by one profile row.**
   - Today the source of truth is `ClientProfile.trial_subscription_used_at`.
   - Future PRs should move trial checks to a verified identity group or otherwise ensure all linked identities share one trial eligibility state.
5. **Profile merge/linking requires explicit user consent or an admin flow.**
   - Backend must not silently merge accounts just because phone/email strings match.
   - A user-facing linking flow should show the target account and require confirmation after OTP verification.
   - Admin merge must be auditable and reversible enough for support operations.

## Current audit findings

### Site `/auth/user-login`

- Finds `User` by lowercased email, exact phone, or lowercased `site_login`.
- Requires active user and a valid password hash.
- Does not create a profile directly during login; `/clients/me` creates a web `ClientProfile` by `user_id` if absent.

### VK `/auth/vk-miniapp-login`

- Finds `ClientProfile` by `ClientProfile.vk_user_id == vk_user_id` only.
- If found, reuses the linked `User`.
- If not found, creates a new client `User` and a new `ClientProfile`.
- Does not compare against existing `User.phone`, `User.email`, or `ClientProfile.contact_email`.

### Telegram `/auth/telegram-miniapp-login`

- Finds `ClientProfile` by `ClientProfile.telegram_user_id == telegram_user_id` only.
- If found, reuses and syncs the linked profile.
- If not found, creates a new client `User` and a new `ClientProfile`.
- Does not compare against existing `User.phone`, `User.email`, or `ClientProfile.contact_email`.

### Client profile `PATCH /clients/me`

- Updates profile fields for the current authenticated user.
- Phone/email updates are uniqueness-checked where they are written to `users`.
- The endpoint does not verify ownership of phone/email and does not link to another profile.

### Trial `/clients/me/trial-subscription`

- Allows trial activation when `ClientProfile.trial_subscription_used_at` is null.
- Writes `trial_subscription_used_at` on the current profile.
- This intentionally remains unchanged in the foundation PR; regression tests document that trial is per profile today.

## Foundation added in this PR

The safe, non-breaking data foundation is:

- Nullable `users.phone_verified_at`.
- Nullable `users.email_verified_at`.
- `client_identity_links` table:
  - `id` primary key.
  - `client_profile_id` foreign key to `client_profiles.id`.
  - `provider` string (`vk`, `telegram`, `site` in the target design).
  - `provider_user_id` string.
  - `linked_at` nullable timestamp.
  - `verified_at` nullable timestamp.
  - `created_at` timestamp.
  - unique constraint on `(provider, provider_user_id)`.

This foundation does **not** change current login behavior and does **not** backfill or auto-link existing rows.

## Non-goals for this PR

- No automatic merge by phone/email.
- No automatic merge between VK and Telegram profiles.
- No changes to auth token format.
- No trial eligibility behavior change.
- No destructive migration or data backfill.

## Next PR plan

1. Add OTP verification endpoints for phone/email.
2. Mark `phone_verified_at` / `email_verified_at` only after successful verification.
3. Add a user-confirmed linking endpoint that can attach the current VK/Telegram identity to an existing verified phone/email profile.
4. Populate `client_identity_links` during confirmed link flows and for new platform logins.
5. Update trial eligibility to prevent repeated trial after verified linking.
6. Add admin-assisted merge/link tooling with audit records for support cases.
