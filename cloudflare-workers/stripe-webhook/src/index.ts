// Stripe webhook proxy — preserves Stripe-Signature header verbatim
// and forwards raw body bytes to the Fly API, where the FastAPI
// signature-verification path is the source of truth.

interface Env {
  FLY_API_BASE: string;
  FLY_API_TOKEN?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "method_not_allowed" }), {
        status: 405, headers: { "Content-Type": "application/json" },
      });
    }
    const sig = request.headers.get("Stripe-Signature");
    if (!sig) {
      return new Response(JSON.stringify({ error: "missing_signature" }), {
        status: 400, headers: { "Content-Type": "application/json" },
      });
    }

    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      "Stripe-Signature": sig,
    };
    if (env.FLY_API_TOKEN) headers["Authorization"] = `Bearer ${env.FLY_API_TOKEN}`;

    let upstream: Response;
    try {
      upstream = await fetch(`${env.FLY_API_BASE}/v1/audit/stripe/webhook`, {
        method: "POST",
        headers,
        body: request.body,  // pass raw bytes — signature is over the body
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: "upstream_unreachable", detail: String(e) }), {
        status: 502, headers: { "Content-Type": "application/json" },
      });
    }

    const body = await upstream.text();
    return new Response(body, {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  },
};
