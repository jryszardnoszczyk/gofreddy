// Scan hosting — serves R2-backed free-scan HTML at reports.gofreddy.ai/scan/<id>/.
// Adds X-Robots-Tag: noindex + Referrer-Policy: no-referrer.

interface Env {
  SCANS: R2Bucket;
  SCAN_PATH_PREFIX: string;
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
    if (request.method !== "GET" && request.method !== "HEAD") {
      return new Response(null, { status: 405 });
    }

    // Path layout: /scan/<id>/ → r2 key `<id>/index.html`
    //              /scan/<id>/<file> → r2 key `<id>/<file>`
    let path = url.pathname.slice(env.SCAN_PATH_PREFIX.length);
    if (!path) return new Response("Not Found", { status: 404 });
    if (path.endsWith("/")) path = `${path}index.html`;

    const obj = await env.SCANS.get(path);
    if (!obj) return new Response("Not Found", { status: 404 });

    const headers = new Headers(SECURITY_HEADERS);
    obj.writeHttpMetadata(headers);
    if (!headers.has("Content-Type")) headers.set("Content-Type", "text/html; charset=utf-8");
    return new Response(obj.body, { headers });
  },
};
