import argparse
import csv
import json
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_CSV = BASE_DIR / "datasets" / "calibration_round1_20.csv"
PORT = 8765

HTML_PAGE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Anotador de Sesgo Político</title>
<style>
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: system-ui, -apple-system, sans-serif;
    background: #0f172a; color: #e2e8f0; line-height: 1.6;
  }
  .topbar {
    position: sticky; top: 0; z-index: 10;
    background: #1e293b; border-bottom: 1px solid #334155;
    padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px;
  }
  .progress-wrap { flex: 1; max-width: 420px; }
  .progress-label { font-size: 13px; color: #94a3b8; margin-bottom: 4px; display: flex; justify-content: space-between; }
  .progress-bar { height: 8px; background: #334155; border-radius: 99px; overflow: hidden; }
  .progress-fill { height: 100%; background: #38bdf8; width: 0%; transition: width 0.2s; }
  .layout {
    max-width: 1200px; margin: 24px auto; padding: 0 20px 40px;
    display: grid; grid-template-columns: 1.6fr 1fr; gap: 24px; align-items: start;
  }
  @media (max-width: 900px) { .layout { grid-template-columns: 1fr; } }
  .card {
    background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px;
  }
  .meta { font-size: 13px; color: #94a3b8; margin-bottom: 8px; display: flex; gap: 12px; align-items: center; }
  .badge { background: #334155; color: #f8fafc; padding: 2px 8px; border-radius: 6px; font-weight: 600; }
  .badge-role { background: #0369a1; color: #e0f2fe; padding: 2px 8px; border-radius: 6px; font-size: 12px; font-weight: 700; }
  h1 { font-size: 22px; margin: 8px 0 12px; color: #f8fafc; line-height: 1.3; }
  .bajada { font-size: 15px; color: #cbd5e1; font-style: italic; margin-bottom: 16px; padding-left: 12px; border-left: 3px solid #38bdf8; }
  .cuerpo { font-size: 15px; color: #e2e8f0; white-space: pre-wrap; max-height: 62vh; overflow-y: auto; padding-right: 8px; }
  .panel { position: sticky; top: 76px; }
  .group { margin-bottom: 18px; }
  .group-title { font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 8px; }
  .btn-row { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
  button.opt {
    padding: 10px 8px; border: 1px solid #475569; border-radius: 8px;
    background: #0f172a; color: #e2e8f0; font-size: 14px; font-weight: 600; cursor: pointer;
    transition: all 0.15s;
  }
  button.opt:hover { border-color: #38bdf8; }
  button.opt.active { background: #0284c7; border-color: #38bdf8; color: #ffffff; }
  button.opt.active-left { background: #dc2626; border-color: #f87171; color: #ffffff; }
  button.opt.active-center { background: #475569; border-color: #94a3b8; color: #ffffff; }
  button.opt.active-right { background: #2563eb; border-color: #60a5fa; color: #ffffff; }
  .actions { display: flex; gap: 10px; margin-top: 20px; }
  .btn-primary {
    flex: 1; padding: 12px; border: none; border-radius: 8px;
    background: #22c55e; color: #052e16; font-size: 15px; font-weight: 700; cursor: pointer;
  }
  .btn-primary:hover { background: #4ade80; }
  .btn-sec {
    padding: 10px 14px; border: 1px solid #475569; border-radius: 8px;
    background: #0f172a; color: #e2e8f0; font-size: 14px; cursor: pointer;
  }
  .btn-sec:hover { border-color: #94a3b8; }
  .status { font-size: 13px; color: #4ade80; min-height: 20px; margin-top: 10px; text-align: center; }
  select {
    background: #0f172a; color: #e2e8f0; border: 1px solid #475569;
    border-radius: 8px; padding: 6px 10px; font-size: 13px;
  }
</style>
</head>
<body>
  <div class="topbar">
    <div style="display:flex; align-items:center; gap:10px;">
      <span style="font-weight:700; font-size:15px;" id="fileName">Cargando...</span>
      <span class="badge-role" id="roleBadge"></span>
    </div>
    <div class="progress-wrap">
      <div class="progress-label">
        <span id="progressText">0 / 0 etiquetadas</span>
        <span id="progressPct">0%</span>
      </div>
      <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
      <select id="jumpSelect"></select>
      <button class="btn-sec" onclick="jumpNextUnlabeled()">Ir a pendiente</button>
    </div>
  </div>

  <div class="layout">
    <div class="card">
      <div class="meta">
        <span class="badge" id="artId"></span>
        <span id="artFecha"></span>
      </div>
      <h1 id="artTitular"></h1>
      <div class="bajada" id="artBajada"></div>
      <div class="cuerpo" id="artCuerpo"></div>
    </div>

    <div class="card panel">
      <div class="group">
        <div class="group-title">Score A — Encuadre y titular</div>
        <div class="btn-row" data-field="score_A">
          <button class="opt" data-val="-1">-1 (Izq)</button>
          <button class="opt" data-val="0">0 (Centro)</button>
          <button class="opt" data-val="1">+1 (Der)</button>
        </div>
      </div>

      <div class="group">
        <div class="group-title">Score B — Lenguaje y tono</div>
        <div class="btn-row" data-field="score_B">
          <button class="opt" data-val="-1">-1 (Izq)</button>
          <button class="opt" data-val="0">0 (Centro)</button>
          <button class="opt" data-val="1">+1 (Der)</button>
        </div>
      </div>

      <div class="group">
        <div class="group-title">Score C — Balance de fuentes</div>
        <div class="btn-row" data-field="score_C">
          <button class="opt" data-val="-1">-1 (Izq)</button>
          <button class="opt" data-val="0">0 (Centro)</button>
          <button class="opt" data-val="1">+1 (Der)</button>
        </div>
      </div>

      <div class="group">
        <div class="group-title">Etiqueta final</div>
        <div class="btn-row" id="etiquetaRow">
          <button class="opt" data-val="LEFT">LEFT</button>
          <button class="opt" data-val="CENTER">CENTER</button>
          <button class="opt" data-val="RIGHT">RIGHT</button>
        </div>
      </div>

      <div class="group">
        <div class="group-title">Confianza</div>
        <div class="btn-row" id="confianzaRow">
          <button class="opt" data-val="ALTA">ALTA</button>
          <button class="opt" data-val="MEDIA">MEDIA</button>
          <button class="opt" data-val="BAJA">BAJA</button>
        </div>
      </div>

      <div class="actions">
        <button class="btn-sec" onclick="prevItem()">← Anterior</button>
        <button class="btn-primary" onclick="saveAndNext()">Guardar y Siguiente →</button>
      </div>
      <div class="status" id="statusMsg"></div>
    </div>
  </div>

<script>
let rows = [];
let labelCol = "etiqueta_a1";
let confCol = "confianza_a1";
let idx = 0;

async function init() {
  const res = await fetch("/api/data");
  const data = await res.json();
  rows = data.rows;
  labelCol = data.label_col;
  confCol = data.conf_col;
  document.getElementById("fileName").textContent = data.filename;
  document.getElementById("roleBadge").textContent = data.role;
  document.getElementById("etiquetaRow").dataset.field = labelCol;
  document.getElementById("confianzaRow").dataset.field = confCol;

  const firstPending = rows.findIndex(r => !r[labelCol]);
  idx = firstPending >= 0 ? firstPending : 0;

  bindButtons();
  renderSelect();
  renderCurrent();
}

function bindButtons() {
  document.querySelectorAll(".btn-row").forEach(row => {
    row.addEventListener("click", e => {
      const btn = e.target.closest("button.opt");
      if (!btn) return;
      const field = row.dataset.field;
      rows[idx][field] = btn.dataset.val;

      if (["score_A", "score_B", "score_C"].includes(field)) {
        autoSuggestLabel();
      }
      renderButtons();
    });
  });

  document.getElementById("jumpSelect").addEventListener("change", e => {
    idx = parseInt(e.target.value, 10);
    renderCurrent();
  });
}

function autoSuggestLabel() {
  const r = rows[idx];
  if (r.score_A !== "" && r.score_B !== "" && r.score_C !== "") {
    const sum = Number(r.score_A) + Number(r.score_B) + Number(r.score_C);
    if (sum <= -1) r[labelCol] = "LEFT";
    else if (sum >= 1) r[labelCol] = "RIGHT";
    else r[labelCol] = "CENTER";
  }
}

function renderSelect() {
  const sel = document.getElementById("jumpSelect");
  sel.innerHTML = "";
  rows.forEach((r, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    const mark = r[labelCol] ? "✓" : "•";
    opt.textContent = `${mark} Noticia #${i + 1} (${r[labelCol] || "pendiente"})`;
    sel.appendChild(opt);
  });
  sel.value = idx;
}

function renderProgress() {
  const done = rows.filter(r => r[labelCol]).length;
  const pct = rows.length ? Math.round((done / rows.length) * 100) : 0;
  document.getElementById("progressText").textContent = `${done} / ${rows.length} etiquetadas`;
  document.getElementById("progressPct").textContent = `${pct}%`;
  document.getElementById("progressFill").style.width = `${pct}%`;
}

function renderButtons() {
  const r = rows[idx];
  document.querySelectorAll(".btn-row").forEach(row => {
    const field = row.dataset.field;
    const val = String(r[field] ?? "");
    row.querySelectorAll("button.opt").forEach(btn => {
      btn.className = "opt";
      if (btn.dataset.val === val) {
        if (val === "LEFT" || val === "-1") btn.classList.add("active-left");
        else if (val === "RIGHT" || val === "1") btn.classList.add("active-right");
        else if (val === "CENTER" || val === "0") btn.classList.add("active-center");
        else btn.classList.add("active");
      }
    });
  });
}

function renderCurrent() {
  const r = rows[idx];
  document.getElementById("artId").textContent = `Noticia #${idx + 1} de ${rows.length} (Modo ciego)`;
  document.getElementById("artFecha").textContent = r.fecha || "Sin fecha";
  document.getElementById("artTitular").textContent = r.titular || "(Sin titular)";
  const bajadaEl = document.getElementById("artBajada");
  bajadaEl.textContent = r.bajada || "";
  bajadaEl.style.display = r.bajada ? "block" : "none";
  document.getElementById("artCuerpo").textContent = r.cuerpo || "";
  document.getElementById("artCuerpo").scrollTop = 0;
  document.getElementById("statusMsg").textContent = "";
  renderButtons();
  renderProgress();
  document.getElementById("jumpSelect").value = idx;
}

async function saveAndNext() {
  const r = rows[idx];
  if (!r[labelCol]) {
    document.getElementById("statusMsg").style.color = "#f87171";
    document.getElementById("statusMsg").textContent = "Selecciona una etiqueta (LEFT, CENTER o RIGHT).";
    return;
  }
  const res = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ index: idx, row: r })
  });
  if (res.ok) {
    renderSelect();
    renderProgress();
    if (idx < rows.length - 1) {
      idx++;
      renderCurrent();
    } else {
      document.getElementById("statusMsg").style.color = "#4ade80";
      document.getElementById("statusMsg").textContent = "Guardado. ¡Llegaste a la última noticia!";
    }
  }
}

function prevItem() {
  if (idx > 0) { idx--; renderCurrent(); }
}

function jumpNextUnlabeled() {
  const next = rows.findIndex((r, i) => i > idx && !r[labelCol]);
  const any = next >= 0 ? next : rows.findIndex(r => !r[labelCol]);
  if (any >= 0) { idx = any; renderCurrent(); }
}

init();
</script>
</body>
</html>
"""


class AppState:
    def __init__(self, csv_path: Path, annotator: str):
        self.csv_path = csv_path
        self.annotator = annotator
        with open(csv_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self.fieldnames = list(reader.fieldnames or [])
            self.rows = list(reader)

        if annotator == "a2":
            self.label_col = "etiqueta_a2"
            self.conf_col = "confianza_a2"
            self.role = "ANOTADOR 2"
        else:
            self.label_col = "etiqueta_a1"
            self.conf_col = "confianza_a1"
            self.role = "ANOTADOR 1"

    def save(self) -> None:
        with open(self.csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)


def make_handler(state: AppState):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def send_bytes(self, status: int, content_type: str, data: bytes):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == "/":
                self.send_bytes(200, "text/html; charset=utf-8", HTML_PAGE.encode("utf-8"))
            elif self.path == "/api/data":
                visible_cols = [
                    "fecha", "titular", "bajada", "cuerpo",
                    "score_A", "score_B", "score_C",
                    state.label_col, state.conf_col,
                ]
                blind_rows = [{c: r.get(c, "") for c in visible_cols} for r in state.rows]
                payload = json.dumps({
                    "filename": state.csv_path.name,
                    "role": state.role,
                    "label_col": state.label_col,
                    "conf_col": state.conf_col,
                    "rows": blind_rows,
                }).encode("utf-8")
                self.send_bytes(200, "application/json; charset=utf-8", payload)
            elif self.path == "/favicon.ico":
                self.send_bytes(204, "image/x-icon", b"")
            else:
                self.send_bytes(404, "text/plain", b"Not Found")

        def do_POST(self):
            if self.path == "/api/save":
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                i = body["index"]
                updated = body["row"]
                for col in ["score_A", "score_B", "score_C", state.label_col, state.conf_col]:
                    if col in updated:
                        state.rows[i][col] = str(updated[col])
                state.save()
                self.send_bytes(200, "application/json", b'{"ok": true}')
            else:
                self.send_bytes(404, "text/plain", b"Not Found")

    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", nargs="?", default=str(DEFAULT_CSV))
    parser.add_argument("--annotator", choices=["a1", "a2"], default="a1")
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"No se encontró {csv_path}")
        sys.exit(1)

    state = AppState(csv_path, annotator=args.annotator)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(state))
    url = f"http://127.0.0.1:{args.port}"
    print(f"Mini-app corriendo en {url} | Archivo: {csv_path.name} | Rol: {state.role}")
    print("Presiona Ctrl+C en esta consola cuando termines.")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido. Todo tu progreso quedó guardado en el CSV.")