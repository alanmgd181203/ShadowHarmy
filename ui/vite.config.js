import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";
import { spawnSync } from "child_process";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataDir = path.resolve(__dirname, "../data");
const rootDir = path.resolve(__dirname, "..");
const cli = path.join(rootDir, "scripts", "set_marcha_cli.py");

function serveDataPlugin() {
  return {
    name: "serve-shadow-data",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url?.startsWith("/data/")) return next();
        const rel = decodeURIComponent(req.url.slice("/data/".length).split("?")[0]);
        const file = path.normalize(path.join(dataDir, rel));
        if (!file.startsWith(dataDir)) {
          res.statusCode = 403;
          res.end("forbidden");
          return;
        }

        // POST marcha → CLI calibrada (no escritura cruda)
        if (req.method === "POST" && rel === "marcha_despliegue.json") {
          const chunks = [];
          req.on("data", (c) => chunks.push(c));
          req.on("end", () => {
            try {
              const raw = Buffer.concat(chunks).toString("utf8");
              const data = JSON.parse(raw);
              if (!data.marcha_id || typeof data.marcha_id !== "string") {
                res.statusCode = 400;
                res.end("marcha_id required");
                return;
              }
              const args = [cli, "--id", data.marcha_id, "--json-out"];
              const dias = data.duracion_dias ?? data.duracionDias;
              if (dias != null && Number(dias) > 0) {
                args.push("--dias", String(dias));
              }
              const eq = data.equity_usd ?? data.equity;
              if (eq != null && Number(eq) > 0) {
                args.push("--equity", String(eq));
              }
              const r = spawnSync("python", args, { cwd: rootDir, encoding: "utf8" });
              if (r.status !== 0) {
                res.statusCode = 400;
                res.end((r.stderr || r.stdout || "set_marcha_cli failed").trim());
                return;
              }
              let payload;
              try {
                payload = JSON.parse(r.stdout || "{}");
              } catch {
                payload = { ok: true, raw: r.stdout };
              }
              res.setHeader("Content-Type", "application/json; charset=utf-8");
              res.end(JSON.stringify({ ok: true, ...payload }));
            } catch (e) {
              res.statusCode = 400;
              res.end(String(e?.message || e));
            }
          });
          return;
        }

        if (req.method !== "GET" && req.method !== "HEAD") {
          res.statusCode = 405;
          res.end("method not allowed");
          return;
        }
        if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
          res.statusCode = 404;
          res.end("not found");
          return;
        }
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        res.setHeader("Cache-Control", "no-store");
        fs.createReadStream(file).pipe(res);
      });
    },
  };
}

export default defineConfig({
  plugins: [react(), serveDataPlugin()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: true,
    fs: {
      allow: [path.resolve(__dirname, "..")],
    },
  },
});
