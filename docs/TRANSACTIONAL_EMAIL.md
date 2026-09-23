# Transactional Email (Brevo)

Last updated: 2026-09-24

## Status

Brevo is the approved Rivexis transactional email provider. The owner-side Brevo account/phone verification is complete. The connected Brevo account currently has SMTP relay enabled and an active Rivexis sender, but production owned-domain authentication has not been certified from the available tooling.

Two branded Brevo templates were created on 2026-09-24 and intentionally left inactive until the production sender/domain and application credential path are certified:

- template `1`: account verification code (`rivexis-auth-verification`)
- template `2`: password reset (`rivexis-auth-password-reset`)

Template IDs are deployment configuration, not secrets. API keys are secrets and must never be committed.

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

`apps/api/rivexis_api/services/transactional_email.py` is the single low-level Brevo send boundary for auth email. It:

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

Until these gates are complete, Brevo remains integrated at the transport boundary but production auth email is not certified as delivered.
