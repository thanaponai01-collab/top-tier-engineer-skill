const $ = (s) => document.querySelector(s);

async function api(path, body) {
  const opts = body ? { method: "POST", body: JSON.stringify(body) } : {};
  const res = await fetch(path, opts);
  return res.json();
}

async function refresh() {
  const q = $("#search").value;
  const items = await api("/api/items" + (q ? "?q=" + encodeURIComponent(q) : ""));
  $("#items").innerHTML = items.map((i) =>
    `<tr><td>${i.name}</td><td>${i.qty} ${i.unit}</td>` +
    `<td><button data-testid="use-btn" data-id="${i.id}" class="use">Use 1</button>` +
    `<button data-testid="restock-btn" data-id="${i.id}" class="restock">+1</button></td></tr>`
  ).join("");
}

$("#items").addEventListener("click", async (e) => {
  const id = e.target.dataset.id;
  if (!id) return;
  const action = e.target.classList.contains("use") ? "use" : "restock";
  await api(`/api/items/${id}/${action}`, { n: 1 });
  refresh();
});

$("#add-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = new FormData(e.target);
  await api("/api/items", { name: f.get("name"), qty: f.get("qty"), min: f.get("min") });
  e.target.reset();
  refresh();
});

$("#shopping-link").addEventListener("click", async (e) => {
  e.preventDefault();
  const list = await api("/api/shopping-list");
  $("#shopping").innerHTML = list.map((i) => `<li>${i.name}: buy ${i.buy} ${i.unit}</li>`).join("");
});

$("#stats-btn").addEventListener("click", async () => {
  $("#stats").textContent = JSON.stringify(await api("/api/stats"), null, 2);
});

$("#search").addEventListener("input", refresh);

document.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== $("#search")) {
    e.preventDefault();
    $("#search").focus();
  }
  if (e.key === "Enter" && e.ctrlKey) {
    $("#add-form").requestSubmit();
  }
});

refresh();
