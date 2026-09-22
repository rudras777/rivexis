const value = process.env.NEXT_PUBLIC_RIVEXIS_API_URL;

if (!value) {
  throw new Error("Set NEXT_PUBLIC_RIVEXIS_API_URL to the deployed HTTPS API origin before deploying the frontend.");
}

let origin;
try {
  origin = new URL(value);
} catch {
  throw new Error("NEXT_PUBLIC_RIVEXIS_API_URL must be a valid HTTPS origin.");
}

if (
  origin.protocol !== "https:" ||
  origin.username ||
  origin.password ||
  origin.pathname !== "/" ||
  origin.search ||
  origin.hash ||
  ["localhost", "127.0.0.1", "::1"].includes(origin.hostname)
) {
  throw new Error("NEXT_PUBLIC_RIVEXIS_API_URL must be a public HTTPS origin without credentials, path, query, or fragment.");
}
