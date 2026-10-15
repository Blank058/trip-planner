// Add/remove location input rows on the create and edit forms.
(function () {
  const list = document.getElementById("location-list");
  const addBtn = document.getElementById("add-location");
  if (!list || !addBtn) return;

  function addRow(value) {
    const row = document.createElement("div");
    row.className = "location-row";
    row.innerHTML =
      '<input name="locations" maxlength="120" placeholder="Another location">' +
      '<button type="button" class="secondary outline remove-location" aria-label="Remove">✕</button>';
    row.querySelector("input").value = value || "";
    list.appendChild(row);
    row.querySelector("input").focus();
  }

  addBtn.addEventListener("click", () => addRow(""));
  list.addEventListener("click", (e) => {
    if (e.target.classList.contains("remove-location")) e.target.closest(".location-row").remove();
  });
})();
