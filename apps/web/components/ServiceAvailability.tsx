"use client";

import {useEffect, useState} from "react";
import {API} from "@/lib/api";

type Availability =
  | {kind: "ready"}
  | {kind: "degraded"; message: string}
  | {kind: "unavailable"; message: string};

const FREE_TIER_REASON = "FastAPI runtime unavailable on the approved free-tier stack";
const RETRY_DELAYS = [5000, 15000];
const UNKNOWN: Availability = {
  kind: "unavailable",
  message: "Application service status could not be verified. Public pages remain available; do not rely on workspace actions until API health is confirmed.",
};

export function ServiceAvailability() {
  const [availability, setAvailability] = useState<Availability | null>(null);
  const [cycle, setCycle] = useState(0);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    let cancelled = false;
    let healthy = false, attempts = 0, generation = 0, dueAt = 0;
    let retryTimer: number | undefined;
    let active: AbortController | null = null;
    const available = () => document.visibilityState !== "hidden" && navigator.onLine !== false;
    const pause = () => {
      generation++;
      window.clearTimeout(retryTimer);
      retryTimer = undefined;
      active?.abort();
      active = null;
      if (!cancelled) setChecking(false);
    };
    const schedule = () => {
      if (cancelled || healthy || active || attempts >= 3 || !available() || retryTimer !== undefined) return;
      if (dueAt > Date.now()) retryTimer = window.setTimeout(() => { retryTimer = undefined; check(); }, dueAt - Date.now());
      else check();
    };
    const check = () => {
      if (cancelled || healthy || active || attempts >= 3 || !available()) return;
      attempts++;
      dueAt = 0;
      const version = ++generation;
      const controller = new AbortController();
      active = controller;
      setChecking(true);
      const current = () => !cancelled && version === generation && active === controller && available();
      const timeout = window.setTimeout(() => controller.abort(), 4000);

      void fetch(`${API}/health`, {
      cache: "no-store",
      credentials: "omit",
      signal: controller.signal,
    })
      .then(async response => {
        if (!response.ok) {
          throw new Error("health request failed");
        }

        const payload: unknown = await response.json();
        if (!payload || typeof payload !== "object" || !("status" in payload) || typeof payload.status !== "string") throw new Error("Invalid health evidence");

        if (!current()) return;
        if (controller.signal.aborted) throw new Error("Health request deadline exceeded");

        const status = payload.status.toLowerCase();
        if (status === "ok" || status === "healthy" || status === "ready") {
          healthy = true;
          setAvailability({kind: "ready"});
          return;
        }

        const freeTierPreview = "reason" in payload && payload.reason === FREE_TIER_REASON;
        setAvailability({
          kind: "degraded",
          message: freeTierPreview
            ? "Application preview: authenticated workspace actions and live analyses are unavailable until the FastAPI runtime is deployed."
            : "Application services are degraded. Public product pages remain available, but authenticated workspace actions may be unavailable.",
        });
      })
      .catch(() => {
        if (current()) setAvailability(UNKNOWN);
      })
      .finally(() => {
        window.clearTimeout(timeout);
        if (!current()) return;
        active = null;
        setChecking(false);
        if (!healthy && attempts < 3) {
          dueAt = Date.now() + RETRY_DELAYS[attempts - 1];
          schedule();
        }
      });
    };
    const changed = () => {
      if (!available()) {
        pause();
        if (navigator.onLine === false) { healthy = false; setAvailability(UNKNOWN); }
      } else schedule();
    };
    document.addEventListener("visibilitychange", changed);
    window.addEventListener("online", changed);
    window.addEventListener("offline", changed);
    changed();

    return () => {
      cancelled = true;
      pause();
      document.removeEventListener("visibilitychange", changed);
      window.removeEventListener("online", changed);
      window.removeEventListener("offline", changed);
    };
  }, [cycle]);

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
      <button className="textButton" type="button" disabled={checking} onClick={() => { setChecking(true); setCycle(value => value + 1); }}>
        {checking ? "Checking service status…" : "Retry service status"}
      </button>
    </div>
  );
}
