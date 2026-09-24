from pathlib import Path
import re

root=Path(__file__).resolve().parents[1]
engine=(root/'apps/api/rivexis_api/models/enums.py').read_text()
ids=re.findall(r'\b([BF][1-5])=',engine)
assert sorted(set(ids))==['B1','B2','B3','B4','B5','F1','F2','F3','F4','F5'],ids
for name in ['PRODUCT_DEFINITION.md','PRODUCT_ARCHITECTURE.md','ENGINE_SPECIFICATIONS.md','DECISION_ENGINE.md','DATA_ARCHITECTURE.md','DATA_PROVIDER_STRATEGY.md','PROVIDER_MATRIX.md','PROVIDER_FALLBACKS.md','DATA_PROVENANCE.md','DATA_FRESHNESS.md','DATA_CONFLICT_POLICY.md','API_SPECIFICATION.md','DATABASE_SCHEMA.md','PROVIDER_ARCHITECTURE.md','SECURITY.md','DESIGN_SYSTEM.md','TEST_PLAN.md','DEPLOYMENT.md','MVP_SCOPE.md','PROTOCOL_ADAPTERS.md','PROTOCOL_DEPLOYMENT_REGISTRY.md','PROTOCOL_HISTORY.md']:
 assert (root/'docs'/name).exists(),name

cloudflare_runtime=(root/'apps/api/cloudflare/src/index.ts').read_text()
for binding in [
 'RIVEXIS_EMAIL_PROVIDER',
 'BREVO_API_KEY',
 'RIVEXIS_BREVO_SENDER_EMAIL',
 'RIVEXIS_BREVO_SENDER_NAME',
 'RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID',
 'RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID',
 'RIVEXIS_BREVO_TIMEOUT_SECONDS',
 'RIVEXIS_BREVO_SANDBOX',
 'RIVEXIS_EMAIL_VERIFICATION_REQUIRED',
 'RIVEXIS_EMAIL_VERIFICATION_TTL_SECONDS',
 'RIVEXIS_PASSWORD_RESET_TTL_SECONDS',
 'RIVEXIS_PUBLIC_WEB_URL',
]:
 assert f'"{binding}"' in cloudflare_runtime, f'missing Cloudflare runtime binding: {binding}'
assert '"RIVEXIS_MIGRATION_DATABASE_URL"' not in cloudflare_runtime, 'migration credential must never enter API runtime container'

print('Rivexis invariants: PASS (10 engines; required docs present; Cloudflare auth/email bindings complete; migration credential isolated)')
