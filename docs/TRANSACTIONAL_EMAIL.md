# Transactional Email (Brevo)

Last reviewed: 2026-10-10

## Current production authentication path

The deployed `supabase/functions/rivexis-api/index.ts` delegates signup, resend, verification and recovery to **Supabase Auth** (`signUp`, `resend`, `verifyOtp`, `resetPasswordForEmail`, `updateUser`). Authentication email uses the existing Supabase SMTP integration with Brevo. The archived FastAPI implementation and Brevo API template IDs described below are not the deployed authentication send boundary. Do not replace SMTP settings or credentials to follow the legacy environment contract.

The retained `rivexis-alert-dispatch` Edge Function separately sends through the Brevo transactional API. Its readiness and API acceptance are distinct from email inbox delivery. These legacy scheduled alerts do not certify continuous monitoring of the new DeFi positions.

Read-only Supabase log audit on 2026-10-10 covered 2026-10-09T06:12:33Z through 2026-10-10T06:12:33Z. It returned 155 auth log rows, zero error/fatal-level rows and zero rows matching the audited SMTP/Brevo/mail-send terms. Logs also contained unsuccessful authentication requests; absence of error-level or mail-related log entries does **not** certify that every request succeeded or that any email was delivered.

The post-release window (2026-10-10T05:41:28Z–06:12:33Z) contained one `/token` 200, seventeen `/user` 200 and one `/user` 403 `bad_jwt`, with no signup, resend, verify or recovery rows. These are aggregate observations, not an attribution to a particular user or test. Fresh verification/recovery inbox completion remains unverified. The Brevo connector's account/template reads failed with an internal connector error; no provider configuration was changed. Credentials, tokens, recipient identities and raw logs were not exported.

## Controlled release certification still required

### Browser audit — 2026-10-10

The existing authenticated Brevo dashboard provided a working read-only path despite the connector's sender read returning Internal error -32603. Transactional usage explicitly showed **Free plan**, **300 emails left until 10/10/2026**, **0 paused emails** and **0 prepaid credits**. No provider settings, subscriptions or credentials were changed.

The visible log window03/10/2026–10/10/2026 contained10 event rows: a confirmation message Sent/Delivered/Opened/Clicked on09/10/2026 (16:38, with later clicks16:40), and a reset message Sent/Delivered on05/10/2026 (14:25). These are dashboard-displayed timestamps; their timezone was not independently established. No October10 email events were present. The summary showed two messages in the last seven days,100% delivered and no hard bounces/blocks. This establishes prior provider delivery evidence, not fresh inbox completion after the current release. Sender/recipient identities, email previews, codes and clicked URLs were not exported; no message was sent or resent. Sanitized observations and cropped delivery/plan screenshots are saved in task outputs/BREVO_BROWSER_AUDIT.json and brevo-*.jpg.

The owner should complete signup/verification or recovery on the existing production site using their own inbox, entering passwords and codes privately. Record the request time, whether the message arrived, and whether the final flow completed; never record codes, reset links or passwords. Correlate that bounded time window with sanitized Auth status/error counts and, when accessible, Brevo acceptance/delivery events. An API `accepted` response, readiness badge, old delivery receipt or absence of SMTP errors is insufficient evidence of fresh inbox delivery. Do not reset another user's password or create an admin session to complete this check.

## Historical implementation record — 2026-09-29

The remainder records the former FastAPI/Brevo API implementation and prior activation evidence. It is retained for rollback and integration context; its account/sender/template statements have not been freshly re-certified through the failing connector.

## Status

Brevo is the approved Rivexis transactional email provider. The owner-side Brevo account/phone verification is complete. The connected account has SMTP relay enabled, an active verified Rivexis sender and a dedicated production API key stored only in Supabase Edge secrets. The current sender uses a freemail domain, so production owned-domain authentication remains unavailable and Brevo warns that DKIM/DMARC compliance is incomplete.

Two branded Brevo templates were created on 2026-09-24 and are active:

- template `1`: account verification code (`rivexis-auth-verification`)
- template `2`: password reset (`rivexis-auth-password-reset`)

Template IDs are deployment configuration, not secrets. API keys are secrets and must never be committed.

The scheduled alert runtime was activated on 2026-09-29 with `BREVO_API_KEY`, sender identity, production-mode and timeout values stored as encrypted Supabase Edge secrets. Both dispatcher and Alerts health endpoints report `SCHEDULED_READY` and `BREVO_READY`. This certifies configuration readiness only; it does not claim provider acceptance or inbox delivery for an alert until a controlled queued alert produces corresponding evidence.

## Environment contract

Transactional email is fail-closed and disabled by default.

```env
RIVEXIS_EMAIL_PROVIDER=disabled
BREVO_API_KEY=
RIVEXIS_BREVO_SENDER_EMAIL=
RIVEXIS_BREVO_SENDER_NAME=Rivexis
RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID=
RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID=
RIVEXIS_BREVO_TIMEOUT_SECONDS=8
RIVEXIS_BREVO_SANDBOX=false
```

Set `RIVEXIS_EMAIL_PROVIDER=brevo` only in an environment where the Brevo API key and verified sender are installed. Each individual flow also refuses to send unless its template ID is present.

`RIVEXIS_BREVO_SANDBOX=true` adds Brevo's `X-Sib-Sandbox: drop` message header. The provider validates and accepts the API request but intentionally sends no email. Rivexis reports this state as `sandbox_accepted`, never `delivered`.

## Delivery semantics

In the archived FastAPI runtime, `apps/api/rivexis_api/services/transactional_email.py` was the low-level Brevo API send boundary for auth email. It:

- sends through `POST https://api.brevo.com/v3/smtp/email`;
- uses Brevo template IDs and request parameters;
- passes a caller-owned `headers.idempotencyKey` so a retry of the same logical message does not intentionally create duplicate mail;
- refuses disabled, unknown, or incomplete provider configuration before making a network request;
- validates recipient and idempotency-key shape locally;
- never reflects provider response bodies into exceptions because auth parameters can contain OTPs or reset URLs;
- treats a successful API response as `accepted` only;
- does not claim `delivered` from a send response, because delivery/bounce state must be established by later provider event/webhook evidence;
- makes sandbox acceptance explicit.

The caller owns flow-specific rate limits, resend cooldowns, OTP/reset-token creation and expiry, and persistent delivery-event lifecycle state. Those higher-level flows must not be exposed until their storage, anti-enumeration behavior, rate limits, token invalidation, and Brevo event handling are implemented and tested.

## Production activation gates

Before enabling real verification or password-reset delivery:

1. certify the production sender and owned-domain authentication;
2. install the Brevo API key only in the runtime secret store;
3. configure the two template IDs and activate only the templates actually used;
4. run sandbox request certification without sending mail;
5. run a controlled real delivery test and verify provider delivery evidence (for example, Brevo transactional events and a test inbox);
6. implement and certify delivery/bounce event ingestion before presenting delivery as anything beyond `accepted`;
7. keep OTP/reset secrets out of application logs, telemetry attributes, audit-detail payloads, and user-visible provider errors.

Supabase Auth recovery delivery has prior Sent + Delivered evidence through the existing Brevo SMTP credential. Alert delivery is configured and scheduled, but a controlled alert acceptance/inbox test remains required before claiming alert delivery beyond readiness.
