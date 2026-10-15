// Response page: location ranking and the availability calendar.
// Both write their state into hidden inputs, so the form posts normally.

// ---------- ranking ----------
const rankList = document.getElementById("rank-list");
const rankingInput = document.getElementById("ranking");

function syncRanking() {
  rankingInput.value = [...rankList.children].map((li) => li.dataset.id).join(",");
}

if (window.Sortable) {
  Sortable.create(rankList, { handle: ".handle", animation: 150, onEnd: syncRanking });
}

rankList.addEventListener("click", (e) => {
  const li = e.target.closest("li");
  if (e.target.classList.contains("move-up") && li.previousElementSibling) {
    rankList.insertBefore(li, li.previousElementSibling);
  } else if (e.target.classList.contains("move-down") && li.nextElementSibling) {
    rankList.insertBefore(li.nextElementSibling, li);
  }
  syncRanking();
});

// ---------- calendar ----------
const daysInput = document.getElementById("days");
const dayCount = document.getElementById("day-count");
const dayButtons = [...document.querySelectorAll(".calendar.pick .day[data-date]")];

function syncDays() {
  const picked = dayButtons.filter((b) => b.classList.contains("selected")).map((b) => b.dataset.date);
  daysInput.value = picked.join(",");
  dayCount.textContent = picked.length ? `${picked.length} day${picked.length === 1 ? "" : "s"} selected` : "";
}

// Press on a day to toggle it; keep the pointer down and drag to paint the same state across days.
let painting = null; // true = selecting, false = clearing, null = not dragging

function paint(btn) {
  btn.classList.toggle("selected", painting);
}

dayButtons.forEach((btn) => {
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    painting = !btn.classList.contains("selected");
    paint(btn);
    btn.releasePointerCapture?.(e.pointerId); // let pointerenter fire on other days (touch)
  });
  btn.addEventListener("pointerenter", () => {
    if (painting !== null) paint(btn);
  });
  // Keyboard users: Enter/Space fire "click" without a pointerdown.
  btn.addEventListener("click", (e) => {
    if (e.detail === 0) {
      btn.classList.toggle("selected");
      syncDays();
    }
  });
});

// Touch screens don't fire pointerenter while dragging, so track the finger manually.
document.addEventListener("pointermove", (e) => {
  if (painting === null || e.pointerType === "mouse") return;
  const el = document.elementFromPoint(e.clientX, e.clientY);
  if (el && el.matches(".calendar.pick .day[data-date]")) paint(el);
});

document.addEventListener("pointerup", () => {
  if (painting !== null) {
    painting = null;
    syncDays();
  }
});

document.getElementById("select-all").addEventListener("click", () => {
  dayButtons.forEach((b) => b.classList.add("selected"));
  syncDays();
});
document.getElementById("clear-all").addEventListener("click", () => {
  dayButtons.forEach((b) => b.classList.remove("selected"));
  syncDays();
});

syncRanking();
syncDays();
