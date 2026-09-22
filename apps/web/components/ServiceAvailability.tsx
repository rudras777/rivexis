"use client";

import {useEffect, useState} from "react";
import {API} from "@/lib/api";

type HealthPayload = {
  status?: string;
  reason?: string;
};

type Availability =
  | {kind: "ready"}
  | {kind: "degraded"; message: string}
  | {kind: "unavailable"; message: string};

const FREE_TIER_REASON = "FastAPI runtime unavailable on the approved free-tier stack";

export function ServiceAvailability() {
  const [availability, setAvailability] = useState<Availability | null>(null);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 4000);

    fetch(`${API}/health`, {
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error("health request failed");
        }

        let payload: HealthPayload = {};
        try {
          payload = (await response.json()) as HealthPayload;
        } catch {
          // A non-JSON health response is not sufficient evidence of readiness.
        }

        if (cancelled) return;

        const status = (payload.status ?? "").toLowerCase();
        if (status === "ok" || status === "healthy" || status === "ready") {
          setAvailability({kind: "ready"});
          return;
        }

        const freeTierPreview = payload.reason === FREE_TIER_REASON;
        setAvailability({
          kind: "degraded",
          message: freeTierPreview
            ? "Free preview: authenticated workspace actions and live analyses are unavailable until the FastAPI runtime is deployed."
            : "Application services are degraded. Public product pages remain available, but authenticated workspace actions may be unavailable.",
        });
      })
      .catch(() => {
        if (!cancelled) {
          setAvailability({
            kind: "unavailable",
            message:
              "Application service status could not be verified. Public pages remain available; do not rely on workspace actions until API health is confirmed.",
          });
        }
      })
      .finally(() => window.clearTimeout(timeout));

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, []);

  if (!availability || availability.kind === "ready") return null;

  return (
    <div
      className={`serviceBanner ${availability.kind}`}
      role="status"
      aria-live="polite"
      data-testid="service-availability"
    >
      <strong>
        {availability.kind === "degraded" ? "Service availability" : "Service status unknown"}
      </strong>
      <span>{availability.message}</span>
    </div>
  );
}
