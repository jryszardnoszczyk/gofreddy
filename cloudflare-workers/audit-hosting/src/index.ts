// Audit hosting — serves R2-backed paid audit HTML+PDF+assets at
// reports.gofreddy.ai/<ulid>/. Routes /scan/* are owned by the
// scan-hosting worker; this worker handles everything else under
// reports.gofreddy.ai.

interface Env {
  AUDITS: R2Bucket;
}

const SECURITY_HEADERS = {
  "X-Robots-Tag": "noindex, nofollow",
  "Referrer-Policy": "no-referrer",
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "private, max-age=300",
};

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    if (url.pathname.startsWith("/scan/")) {
      // Defensive — route table should have already dispatched to scan-hosting.
      return new Response("Routed to wrong worker", { status: 404 });
    }
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response(null, { status: 405 });
    }

    let path = url.pathname.slice(1);  // strip leading /
    if (!path) return new Response("Not Found", { status: 404 });
    if (path.endsWith("/")) path = `${path}report.html`;

    const obj = await env.AUDITS.get(path);
    if (!obj) return new Response("Not Found", { status: 404 });

    const headers = new Headers(SECURITY_HEADERS);
    obj.writeHttpMetadata(headers);
    if (!headers.has("Content-Type")) {
      // Default by extension
      if (path.endsWith(".pdf")) headers.set("Content-Type", "application/pdf");
      else if (path.endsWith(".html")) headers.set("Content-Type", "text/html; charset=utf-8");
      else headers.set("Content-Type", "application/octet-stream");
    }
    return new Response(obj.body, { headers });
  },
};
