/* ../NauTrader_Helm/payments-core/dashboard/src/auth/helmAuthBridge.ts */

import { setAccessToken } from "../api/client";

function resolveHelmOrigin(): string | null {
  const value = new URLSearchParams(window.location.search).get("helmOrigin");
  if (!value) return null;

  try {
    const url = new URL(value);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    return url.origin;
  } catch {
    return null;
  }
}

const HELM_ORIGIN = resolveHelmOrigin();
const AUTH_REQUEST_TYPE = "payments-core:auth-request";
const AUTH_RESPONSE_TYPE = "helm:auth-response";
const AUTH_TIMEOUT_MS = 10_000;

export type HelmAuthResult =
  | { mode: "demo" }
  | { mode: "authenticated" }
  | { mode: "error"; message: string };

type AuthResponse = {
  type: typeof AUTH_RESPONSE_TYPE;
  authenticated: boolean;
  accessToken?: string;
};

function isAuthResponse(value: unknown): value is AuthResponse {
  if (typeof value !== "object" || value === null) return false;

  const response = value as Record<string, unknown>;

  return (
    response.type === AUTH_RESPONSE_TYPE &&
    typeof response.authenticated === "boolean" &&
    (response.accessToken === undefined ||
      typeof response.accessToken === "string")
  );
}

export function initializeHelmAuth(): Promise<HelmAuthResult> {
  setAccessToken(null);

  if (!window.opener) {
    return Promise.resolve({ mode: "demo" });
  }

  if (!HELM_ORIGIN) {
    return Promise.resolve({
      mode: "error",
      message: "Helm origin is missing or invalid.",
    });
  }

  return new Promise((resolve) => {
    let settled = false;

    const finish = (result: HelmAuthResult): void => {
      if (settled) return;
      settled = true;
      window.clearTimeout(timeoutId);
      window.removeEventListener("message", handleMessage);
      resolve(result);
    };

    const handleMessage = (event: MessageEvent<unknown>): void => {
      if (event.origin !== HELM_ORIGIN) return;
      if (event.source !== window.opener) return;
      if (!isAuthResponse(event.data)) return;

      if (
        event.data.authenticated &&
        typeof event.data.accessToken === "string" &&
        event.data.accessToken.trim().length > 0
      ) {
        setAccessToken(event.data.accessToken);
        finish({ mode: "authenticated" });
        return;
      }

      finish({
        mode: "error",
        message: "Helm did not provide an authenticated session.",
      });
    };

    const timeoutId = window.setTimeout(() => {
      finish({
        mode: "error",
        message: "Timed out waiting for the Helm authentication response.",
      });
    }, AUTH_TIMEOUT_MS);

    window.addEventListener("message", handleMessage);

    try {
      window.opener.postMessage(
        { type: AUTH_REQUEST_TYPE },
        HELM_ORIGIN,
      );
    } catch {
      finish({
        mode: "error",
        message: "Unable to communicate with Helm.",
      });
    }
  });
}
