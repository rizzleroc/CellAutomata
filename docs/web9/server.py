#!/usr/bin/env python3
"""
server.py — web9 render backend (the real bridge).

Serves the web9 site AND a render API on one origin (no CORS pain):

  GET  /                     -> index.html (and all static assets)
  GET  /api/health           -> { ok, export_mesh }
  POST /api/render           -> { job, status:"queued" }
       body: { F, k, frames, frame_step, n, seed }
  GET  /api/job/<id>         -> { status, ... , bin_url } when done
  GET  /api/job/<id>/cleavage.bin -> the freshly-simulated geometry

A render job runs tools/unreal/export_mesh.py (the real 3D Gray-Scott + marching
cubes science bridge) with the requested parameters, then bundles the OBJ
sequence into the browser binary the hero loads. The full Unreal 5.8 cinema
render still runs on a GPU workstation; this server does the deterministic
science and hands the web UI a real, freshly-simulated dividing cell.

Run:   cd docs/web9 && python3 server.py        (default port 8770)
Needs: numpy + scikit-image (+ scipy) for export_mesh.py. No web framework.
"""

import json
import os
import struct
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT_MESH = os.path.normpath(os.path.join(HERE, "..", "..", "tools", "unreal", "export_mesh.py"))
JOBS_DIR = os.path.join(HERE, "jobs")
PORT = int(os.environ.get("PORT", "8770"))

JOBS = {}
JOBS_LOCK = threading.Lock()


# ----------------------------------------------------------------------------
def bundle_objs(mesh_dir, out_bin, stride=1):
    """Parse the OBJ sequence -> one little-endian binary the hero loads:
    magic(u32) frameCount(u32); per frame: vc,tc(u32), pos[vc*3]f32, nrm[vc*3]f32, idx[tc*3]u32."""
    files = sorted(f for f in os.listdir(mesh_dir) if f.endswith(".obj"))[::stride]
    out = bytearray()
    out += struct.pack("<II", 0x4D435631, len(files))
    for fn in files:
        V, N, F = [], [], []
        with open(os.path.join(mesh_dir, fn)) as fh:
            for ln in fh:
                if ln[:2] == "v ":
                    V.append(tuple(float(t) for t in ln.split()[1:4]))
                elif ln[:3] == "vn ":
                    N.append(tuple(float(t) for t in ln.split()[1:4]))
                elif ln[:2] == "f ":
                    F.append(tuple(int(t.split("//")[0]) - 1 for t in ln.split()[1:4]))
        if len(N) < len(V):
            N += [(0.0, 0.0, 1.0)] * (len(V) - len(N))
        out += struct.pack("<II", len(V), len(F))
        for v in V:
            out += struct.pack("<fff", *v)
        for n in N[:len(V)]:
            out += struct.pack("<fff", *n)
        for f in F:
            out += struct.pack("<III", *f)
    with open(out_bin, "wb") as fh:
        fh.write(out)
    return len(files), len(out)


def run_job(job_id, params):
    job = JOBS[job_id]
    try:
        job_dir = os.path.join(JOBS_DIR, job_id)
        mesh_dir = os.path.join(job_dir, "mesh")
        os.makedirs(mesh_dir, exist_ok=True)

        env = dict(os.environ)
        env["OUTDIR"] = mesh_dir
        env["N"] = str(params["n"])
        env["F"] = str(params["F"])
        env["k"] = str(params["k"])
        env["FRAMES"] = str(params["frames"])
        env["FRAME_STEP"] = str(params["frame_step"])
        env["SEED"] = str(params["seed"])
        env["STEPS"] = str(params.get("steps", 700))

        job["status"] = "simulating"
        job["log"].append("export_mesh.py N=%(n)s F=%(F)s k=%(k)s frames=%(frames)s" % params)
        t0 = time.time()
        proc = subprocess.run([sys.executable, EXPORT_MESH], env=env,
                              capture_output=True, text=True, cwd=job_dir, timeout=240)
        for line in (proc.stderr or "").strip().splitlines()[-8:]:
            job["log"].append(line)
        if proc.returncode != 0:
            job["status"] = "error"
            job["log"].append("export_mesh failed rc=%d" % proc.returncode)
            return

        job["status"] = "bundling"
        n_frames, nbytes = bundle_objs(mesh_dir, os.path.join(job_dir, "cleavage.bin"))
        job["frames"] = n_frames
        job["bytes"] = nbytes
        job["sim_seconds"] = round(time.time() - t0, 1)
        job["bin_url"] = "/api/job/%s/cleavage.bin" % job_id
        job["status"] = "done"
        job["log"].append("bundled %d frames, %d bytes -> %s" % (n_frames, nbytes, job["bin_url"]))
    except Exception as e:  # noqa: BLE001
        job["status"] = "error"
        job["log"].append("exception: %s" % e)


# ----------------------------------------------------------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/api/health":
            return self._send(200, {"ok": True, "export_mesh": os.path.isfile(EXPORT_MESH)})
        if path.startswith("/api/job/"):
            rest = path[len("/api/job/"):]
            if rest.endswith("/cleavage.bin"):
                jid = rest[:-len("/cleavage.bin")]
                fp = os.path.join(JOBS_DIR, jid, "cleavage.bin")
                if os.path.isfile(fp):
                    with open(fp, "rb") as fh:
                        return self._send(200, fh.read(), "application/octet-stream")
                return self._send(404, {"error": "no bin"})
            with JOBS_LOCK:
                job = JOBS.get(rest)
            return self._send(200, job) if job else self._send(404, {"error": "no job"})
        return self._serve_static(path)

    def do_POST(self):
        if self.path.split("?")[0] != "/api/render":
            return self._send(404, {"error": "not found"})
        n = int(self.headers.get("Content-Length", "0"))
        try:
            req = json.loads(self.rfile.read(n) or b"{}")
        except Exception:  # noqa: BLE001
            req = {}
        params = {
            "F": float(req.get("F", 0.030)),
            "k": float(req.get("k", 0.067)),
            "frames": max(2, min(120, int(req.get("frames", 48)))),
            "frame_step": max(2, min(40, int(req.get("frame_step", 12)))),
            "n": max(40, min(96, int(req.get("n", 64)))),
            "seed": int(req.get("seed", 7)),
            "steps": max(200, min(1500, int(req.get("steps", 700)))),
        }
        job_id = uuid.uuid4().hex[:8]
        with JOBS_LOCK:
            JOBS[job_id] = {"id": job_id, "status": "queued", "params": params, "log": []}
        threading.Thread(target=run_job, args=(job_id, params), daemon=True).start()
        return self._send(202, {"job": job_id, "status": "queued", "params": params})

    def _serve_static(self, path):
        if path == "/":
            path = "/index.html"
        fp = os.path.normpath(os.path.join(HERE, path.lstrip("/")))
        if not fp.startswith(HERE) or not os.path.isfile(fp):
            return self._send(404, {"error": "not found"})
        ext = os.path.splitext(fp)[1].lower()
        ctype = {".html": "text/html", ".js": "application/javascript", ".css": "text/css",
                 ".png": "image/png", ".gif": "image/gif", ".bin": "application/octet-stream",
                 ".json": "application/json"}.get(ext, "application/octet-stream")
        with open(fp, "rb") as fh:
            self._send(200, fh.read(), ctype)

    def log_message(self, *a):  # quieter
        pass


def main():
    os.makedirs(JOBS_DIR, exist_ok=True)
    print("web9 render backend on http://localhost:%d" % PORT)
    print("  site:   http://localhost:%d/" % PORT)
    print("  health: http://localhost:%d/api/health" % PORT)
    print("  export_mesh.py: %s (%s)" % (EXPORT_MESH, "found" if os.path.isfile(EXPORT_MESH) else "MISSING"))
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
