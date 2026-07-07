# VK Mini App Backend Readiness Audit

**Repository:** `Kosmos327/fed_women_club_WEB`  
**Target Mini App:** `Bloom Club` (`VK_APP_ID=54600832`, `https://vk.com/app54600832`)  
**Audit date:** 2026-05-20  
**Scope:** only current `fed_women_club_WEB` codebase; no code changes to backend/frontend logic.

---

## Executive summary

Backend is **partially ready** for VK Mini App:

- ✅ There is a client domain model with `vk_user_id` and bot-oriented VK endpoints already in production path.
- ✅ Unified user JWT auth for client endpoints already exists (`/api/v1/auth/user-login`, bearer token with `sub=user:{id}`).
- ✅ Key client data endpoints needed by Mini App already exist and are reusable.
- ⚠️ There is **no dedicated VK Mini App login endpoint** and **no VK launch parameter signature validation** in current code.
- ⚠️ CORS must be explicitly configured for Mini App webview origins before production launch.

**Bottom line:** Backend is **not fully ready for secure Mini App auth flow yet**; requires adding `POST /api/v1/auth/vk-miniapp-login` (with VK signature verification + token issuing), plus rollout hardening.

---

## 1) Current client auth architecture

Current architecture is split into two auth contours:

1. **Admin auth** (`/api/v1/auth/login`) based on `AdminUser` token subject as numeric admin id.
2. **Unified user auth** (`/api/v1/auth/user-login`) for `User` table (`admin|partner|client`) with bearer JWT subject format `user:{id}`.

Client cabinet APIs (including target Mini App reusable endpoints) are protected by `require_client`, which resolves current user from bearer token and checks role `client`.

Implication for Mini App: Mini App can consume client endpoints **if** it receives a valid unified user token.

---

## 2) Where `vk_user_id` is stored

- Primary storage: `client_profiles.vk_user_id` (nullable, unique, indexed).
- Also present in `client_password_setup_tokens.vk_user_id` as auxiliary onboarding context.

This is sufficient as a stable link key between VK identity and internal client profile.

---

## 3) Existing VK-bot endpoints

Router prefix: `/api/v1/bot/vk`.

Implemented endpoints:

- `POST /api/v1/bot/vk/onboard-client`
  - Upserts/creates client user/profile by `vk_user_id`, optional city/email/phone.
  - Returns bearer access token + user + profile + password setup metadata.
- `POST /api/v1/bot/vk/token`
  - Exchanges `vk_user_id` to bearer token **if profile already linked**.
- `POST /api/v1/bot/vk/exchange-link-code`
  - Exchanges one-time VK link code + `vk_user_id` into linked profile and returns bearer token.

All three are protected by `require_bot_api_token` (service bearer token), i.e. trusted server-to-server flow.

---

## 4) Can client session be restored by `vk_user_id`

**Yes, technically already possible**:

- `/api/v1/bot/vk/token` finds `ClientProfile` by `vk_user_id` and issues access token for linked active `client` user.

But for Mini App this is not directly sufficient as-is because endpoint is bot-token protected and does not verify VK launch params from Mini App client runtime.

---

## 5) Is VK launch params signature verification present

**No.** During audit, no implementation found for:

- parsing `vk_` launch params,
- canonicalization for VK sign check,
- signature/hash verification (`sign`),
- freshness/anti-replay checks for launch payload.

This is the main security gap for direct Mini App login.

---

## 6) Endpoints Mini App can reuse now

The following endpoints already exist and map well to Mini App client UX:

1. `GET /api/v1/clients/me`
2. `GET /api/v1/clients/me/subscription`
3. `GET /api/v1/clients/catalog/partners`
4. `GET /api/v1/clients/me/verifications`
5. `POST /api/v1/clients/partners/{id}/verify`

Condition: Mini App must first obtain standard client bearer token.

---

## 7) What to add for `POST /api/v1/auth/vk-miniapp-login`

Recommended contract (high-level):

### Request
- Raw VK launch/auth payload from Mini App (includes `vk_user_id` and `sign` + context fields).

### Required backend logic
1. Validate required params presence.
2. Verify VK signature strictly by official algorithm.
3. Validate timestamp/freshness (anti-replay window).
4. Resolve `ClientProfile` by `vk_user_id`.
5. If linked active client user exists: issue unified bearer token.
6. If not linked:
   - either create lightweight pre-onboard client or return explicit status requiring onboarding/link flow.
7. Return token response aligned with existing unified auth schema.
8. Audit-log login attempt (success/failure reason, request id, vk_user_id masked where needed).

### Response (candidate)
- `200`: `{ access_token, token_type, user, client? }`
- `401/403`: invalid VK signature / stale payload
- `404/409`: no linked profile / conflict cases

---

## 8) CORS / allowed origins

CORS settings are environment-driven via `BACKEND_CORS_ORIGINS` list parser.

Important findings:

- Default origins are local dev (`localhost:5173`, `127.0.0.1:5173`).
- In current `main.py`, explicit `CORSMiddleware` wiring was not found during audit snippet review.

Actions before Mini App rollout:

1. Confirm whether middleware is configured elsewhere; if absent, add in a dedicated backend PR.
2. Add production origins for site + Mini App host surface used by VK webview deployment.
3. Keep strict allowlist (no wildcard in prod).
4. Validate credentials/headers/methods policy for bearer auth calls.

---

## 9) Security risks

1. **No VK signature verification path** for Mini App login (critical).
2. Potential replay risk if launch params are accepted without timestamp nonce checks.
3. `vk_user_id`-based token issuance endpoint exists for trusted bot token; must never be exposed to public client context.
4. CORS misconfiguration risk if permissive origin policy is used for bearer APIs.
5. Account-link conflicts: wrong linking or stale link code usage (partially mitigated by status/expiry checks already present).
6. Need consistent logging/rate limiting for login endpoint to detect abuse.

---

## 10) Phased implementation plan

### Phase 0 — Audit completion (current)
- Confirm reusable endpoints and gaps.
- Freeze this document as baseline.

### Phase 1 — Secure Mini App auth entrypoint
- Add `POST /api/v1/auth/vk-miniapp-login`.
- Implement VK signature + freshness validation.
- Issue standard unified bearer token for client role.

### Phase 2 — Linking/onboarding consistency
- Define behavior for unlinked `vk_user_id`:
  - auto-onboard or explicit link-required response.
- Reuse existing bot/web link-code mechanics where appropriate.

### Phase 3 — Deployment hardening
- Finalize CORS allowlist for production origins.
- Add rate limits, structured audit logs, monitoring alerts.
- Security test cases for invalid sign, replay, tampered params.

### Phase 4 — Mini App integration
- Wire Mini App login call to new endpoint.
- Reuse existing client endpoints (`me/subscription/catalog/verifications/verify`).
- Run UAT with real VK launch payloads and rollback plan.

---

## Final readiness verdict

- **Current state:** backend is **functionally close**, but **security-incomplete** for direct VK Mini App auth.
- **Ready now for Mini App production login:** **No**.
- **Ready after minimal backend addition:** **Yes**, after implementing secure `vk-miniapp-login` and CORS hardening.

