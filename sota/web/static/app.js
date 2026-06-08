const state = { items: [], catalog: { combos: [], artifacts: [], tablets: [] } };
const $ = (id) => document.getElementById(id);
const showErr = (m) => { $("err").textContent = m || ""; };

function keyType(key) {
  if (state.catalog.tablets.some((t) => t.key === key)) return "tablet";
  if (state.catalog.artifacts.some((a) => a.key === key)) return "artifact";
  return "empty";
}

function renderItems() {
  const box = $("items");
  box.innerHTML = "";
  state.items.forEach((it, i) => {
    const row = document.createElement("div");
    row.className = "row" + (it.confidence < 0.9 ? " low" : "");
    const inp = document.createElement("input");
    inp.value = it.key; inp.setAttribute("list", "catalog");
    inp.onchange = () => { it.key = inp.value; it.type = keyType(inp.value); };
    const conf = document.createElement("span");
    conf.className = "conf";
    conf.textContent = it.confidence != null ? it.confidence.toFixed(2) : "";
    const del = document.createElement("button");
    del.textContent = "삭제";
    del.onclick = () => { state.items.splice(i, 1); renderItems(); };
    row.append(inp, conf, del);
    box.appendChild(row);
  });
  $("solveBtn").disabled = !$("combo").value;
}

async function loadCatalog() {
  const r = await fetch("/api/catalog");
  state.catalog = await r.json();
  $("combo").innerHTML = state.catalog.combos
    .map((c) => `<option value="${c.key}">${c.name} (${c.key})</option>`).join("");
  $("catalog").innerHTML = [...state.catalog.tablets, ...state.catalog.artifacts]
    .map((x) => `<option value="${x.key}">${x.name}</option>`).join("");
  renderItems();
}

async function recognize() {
  showErr("");
  const f = $("file").files[0];
  if (!f) { showErr("파일을 선택하세요."); return; }
  const fd = new FormData(); fd.append("file", f);
  const r = await fetch("/api/recognize", { method: "POST", body: fd });
  if (!r.ok) { showErr("인식 실패: " + (await r.json()).detail); return; }
  const body = await r.json();
  state.items = body.items.filter((it) => it.type !== "empty");
  renderItems();
}

function addItem() {
  const key = $("addKey").value.trim();
  if (!key) return;
  state.items.push({ key, type: keyType(key), confidence: 1.0 });
  $("addKey").value = "";
  renderItems();
}

async function solve() {
  showErr("");
  const payload = {
    tablets: state.items.filter((i) => i.type === "tablet").map((i) => i.key),
    artifacts: state.items.filter((i) => i.type === "artifact").map((i) => i.key),
    combo: $("combo").value,
    slots: parseInt($("slots").value, 10),
    seed: 42, generations: 60, pop_size: 80,
  };
  $("solveBtn").disabled = true; $("solveBtn").textContent = "계산 중…";
  const r = await fetch("/api/solve",
    { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload) });
  $("solveBtn").disabled = false; $("solveBtn").textContent = "추천 배치 계산";
  if (!r.ok) { showErr("계산 실패: " + (await r.json()).detail); return; }
  const s = await r.json();
  $("result").innerHTML =
    `<p>점수 <b>${s.score}</b> (콤보 ${s.stages}단계 × 1000 + 레벨 ${s.level_sum})</p>` +
    `<img src="data:image/png;base64,${s.image_base64}">`;
}

$("recognizeBtn").onclick = recognize;
$("addBtn").onclick = addItem;
$("solveBtn").onclick = solve;
$("combo").onchange = renderItems;
loadCatalog();
