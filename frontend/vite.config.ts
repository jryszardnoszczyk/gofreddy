import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

const devProxyTarget = process.env.VITE_DEV_PROXY_TARGET ?? "http://127.0.0.1:8000";

function createSseProxyConfig(target: string) {
  return {
    target,
    changeOrigin: true,
    // BUG-17: Prevent http-proxy from auto-piping responses so we
    // can flush SSE chunks immediately without double-writes.
    selfHandleResponse: true,
    configure: (proxy: import("http-proxy").Server) => {
      proxy.on("proxyRes", (proxyRes, _req, res) => {
        const httpRes = res as import("http").ServerResponse;
        // Copy status code and headers for all responses
        httpRes.writeHead(proxyRes.statusCode ?? 200, proxyRes.headers);

        if (
          proxyRes.headers["content-type"]?.includes("text/event-stream")
        ) {
          // SSE: write chunks directly as they arrive (no buffering)
          proxyRes.on("data", (chunk: Buffer) => {
            if (!httpRes.writableEnded) httpRes.write(chunk);
          });
          proxyRes.on("end", () => {
            if (!httpRes.writableEnded) httpRes.end();
          });
        } else {
          // Non-SSE: pipe normally
          proxyRes.pipe(httpRes);
        }
      });
      // Prevent unhandled proxy errors from crashing Vite
      proxy.on("error", (err, _req, res) => {
        console.error("[vite] proxy error:", err.message);
        const httpRes = res as import("http").ServerResponse;
        if (!httpRes.headersSent) {
          httpRes.writeHead(502, { "Content-Type": "application/json" });
        }
        if (!httpRes.writableEnded) {
          httpRes.end(JSON.stringify({ error: { code: "proxy_error", message: "Backend unavailable" } }));
        }
      });
      // Forward client disconnects to the backend
      proxy.on("proxyReq", (proxyReq, _req, res) => {
        (res as NodeJS.WritableStream).on("close", () => {
          if (!(res as NodeJS.WritableStream).writableEnded) {
            proxyReq.destroy();
          }
        });
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 3001,
    proxy: {
      "/v1": createSseProxyConfig(devProxyTarget),
      "/v2": createSseProxyConfig(devProxyTarget),
      "/health": devProxyTarget,
      "/webhooks": devProxyTarget,
    },
  },
});
