import { Container, getContainer } from "@cloudflare/containers";

const TRANSACTIONAL_EMAIL_BINDINGS = [
  "RIVEXIS_EMAIL_PROVIDER",
  "BREVO_API_KEY",
  "RIVEXIS_BREVO_SENDER_EMAIL",
  "RIVEXIS_BREVO_SENDER_NAME",
  "RIVEXIS_BREVO_VERIFICATION_TEMPLATE_ID",
  "RIVEXIS_BREVO_PASSWORD_RESET_TEMPLATE_ID",
  "RIVEXIS_BREVO_TIMEOUT_SECONDS",
  "RIVEXIS_BREVO_SANDBOX",
] as const;

const OPTIONAL_RUNTIME_BINDINGS = [
  ...TRANSACTIONAL_EMAIL_BINDINGS,
  "DUNE_API_KEY",
  "ETHERSCAN_API_KEY",
  "ALCHEMY_API_KEY",
  "QUICKNODE_URL",
  "QUICKNODE_URL_TEMPLATE",
  "ETHEREUM_RPC_URL",
  "BASE_RPC_URL",
  "ARBITRUM_RPC_URL",
  "OPTIMISM_RPC_URL",
  "POLYGON_RPC_URL",
  "TENDERLY_ACCESS_KEY",
  "TENDERLY_ACCOUNT",
  "TENDERLY_PROJECT",
  "BLOCKAID_API_KEY",
  "BLOCKAID_CLIENT_API_KEY",
  "BLOCKAID_BASE_URL",
  "HYPERNATIVE_API_KEY",
  "HYPERNATIVE_BASE_URL",
  "HYPERNATIVE_WEBHOOK_SECRET",
  "LIFI_API_KEY",
  "NANSEN_API_KEY",
  "NANSEN_BASE_URL",
  "ARKHAM_API_KEY",
  "ARKHAM_BASE_URL",
  "COINGECKO_API_KEY",
  "COINMARKETCAP_API_KEY",
  "KAIKO_API_KEY",
  "GLASSNODE_API_KEY",
  "TOKEN_TERMINAL_API_KEY",
  "MESSARI_API_KEY",
  "GAUNTLET_API_KEY",
  "CHAOS_LABS_API_KEY",
  "THEGRAPH_API_KEY",
  "RIVEXIS_ALERT_WEBHOOK_URL",
  "RIVEXIS_ALERT_WEBHOOK_SCOPE",
  "RIVEXIS_ALERT_WEBHOOK_SECRET",
] as const;

type OptionalRuntimeBinding = (typeof OPTIONAL_RUNTIME_BINDINGS)[number];

type RivexisWorkerEnv = {
  RIVEXIS_API_CONTAINER: DurableObjectNamespace<RivexisApiContainer>;
  DATABASE_URL?: string;
  RIVEXIS_AUTH_SECRET?: string;
  RIVEXIS_ALLOWED_ORIGINS?: string;
  RIVEXIS_ARKHAM_LICENSE_APPROVED?: string;
} & Partial<Record<OptionalRuntimeBinding, string>>;

function requireBinding(env: RivexisWorkerEnv, name: "DATABASE_URL" | "RIVEXIS_AUTH_SECRET" | "RIVEXIS_ALLOWED_ORIGINS"): string {
  const value = env[name]?.trim();
  if (!value) {
    throw new Error(`Missing required Worker secret: ${name}`);
  }
  return value;
}

function containerEnvironment(env: RivexisWorkerEnv): Record<string, string> {
  const result: Record<string, string> = {
    RIVEXIS_ENV: "production",
    DATABASE_URL: requireBinding(env, "DATABASE_URL"),
    RIVEXIS_AUTH_SECRET: requireBinding(env, "RIVEXIS_AUTH_SECRET"),
    RIVEXIS_ALLOWED_ORIGINS: requireBinding(env, "RIVEXIS_ALLOWED_ORIGINS"),
    ENABLE_DEMO_ADAPTER: "false",
    RIVEXIS_ALLOW_DIRECT_ORG_MEMBER_ADD: "false",
    RIVEXIS_AUTH_RATE_LIMIT_BACKEND: "postgres",
    RIVEXIS_PROVIDER_CONTROL_BACKEND: "postgres",
    RIVEXIS_AUTO_CREATE_SCHEMA: "false",
  };

  for (const name of OPTIONAL_RUNTIME_BINDINGS) {
    const value = env[name]?.trim();
    if (value) result[name] = value;
  }
  if (env.RIVEXIS_ARKHAM_LICENSE_APPROVED === "true") {
    result.RIVEXIS_ARKHAM_LICENSE_APPROVED = "true";
  }
  return result;
}

export class RivexisApiContainer extends Container<RivexisWorkerEnv> {
  defaultPort = 8000;
  requiredPorts = [8000];
  sleepAfter = "10m";
  pingEndpoint = "localhost/health";

  constructor(ctx: DurableObjectState<{}>, env: RivexisWorkerEnv) {
    super(ctx, env);
    this.envVars = containerEnvironment(env);
  }

  override onError(error: unknown): never {
    console.error("Rivexis API container error", error);
    throw error;
  }
}

export default {
  async fetch(request: Request, env: RivexisWorkerEnv): Promise<Response> {
    try {
      return await getContainer(env.RIVEXIS_API_CONTAINER, "primary").fetch(request);
    } catch (error) {
      console.error("Rivexis API proxy error", error);
      return Response.json(
        { detail: "API service temporarily unavailable" },
        { status: 503, headers: { "Retry-After": "5" } },
      );
    }
  },
} satisfies ExportedHandler<RivexisWorkerEnv>;
