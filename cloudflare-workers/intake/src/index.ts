// Form intake worker — proxies gofreddy.ai/api/scan-request → Fly API.
//
// Validates basic shape (url + email present), CORS-preflights for the
// public form domain, and forwards as JSON. Failures upstream are
// surfaced as 502 so the form UI can retry without ambiguity.

interface Env {
  FLY_API_BASE: string;
  FLY_API_TOKEN?: string;
}

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "https://gofreddy.ai",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
  "Access-Control-Max-Age": "86400",
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: CORS_HEADERS });
    }
    if (request.method !== "POST") {
      return json({ error: "method_not_allowed" }, 405);
    }

    let body: any;
    try {
      body = await request.json();
    } catch {
      return json({ error: "invalid_json" }, 400);
    }
    if (!body?.url || !body?.email) {
      return json({ error: "missing_fields", required: ["url", "email"] }, 422);
    }

    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (env.FLY_API_TOKEN) headers["Authorization"] = `Bearer ${env.FLY_API_TOKEN}`;

    let upstream: Response;
    try {
      upstream = await fetch(`${env.FLY_API_BASE}/v1/scan/request`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });
    } catch (e) {
      return json({ error: "upstream_unreachable", detail: String(e) }, 502);
    }

    const upstreamBody = await upstream.text();
    return new Response(upstreamBody, {
      status: upstream.status,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  },
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}
