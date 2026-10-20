// form.js — powers the portal form:
//   1. Loads Ghana's regions into the first select asynchronously.
//   2. Loads the matching districts into the second select when a region
//      is chosen (the dependent-dropdown pattern).
//   3. Runs a final check before the form is submitted.

// Grab the two dependent select boxes once.
const regionSelect = document.getElementById("region");
const districtSelect = document.getElementById("district");

// Small helper: replace a select's options with a fresh list.
function fillSelect(selectEl, items, placeholder) {
  selectEl.innerHTML = "";
  const first = document.createElement("option");
  first.value = "";
  first.textContent = placeholder;
  selectEl.appendChild(first);

  items.forEach((item) => {
    const opt = document.createElement("option");
    opt.value = item;
    opt.textContent = item;
    selectEl.appendChild(opt);
  });
}

// 1. Load the list of regions from the server (async/await + fetch).
async function loadRegions() {
  try {
    const response = await fetch("/api/regions");
    const regions = await response.json();
    fillSelect(regionSelect, regions, "Select your region");
  } catch (err) {
    fillSelect(regionSelect, [], "Could not load regions");
    console.error("Failed to load regions:", err);
  }
}

// 2. When the region changes, fetch that region's districts.
async function loadDistricts(region) {
  if (!region) {
    districtSelect.disabled = true;
    fillSelect(districtSelect, [], "Select a region first");
    return;
  }
  try {
    districtSelect.disabled = true;
    fillSelect(districtSelect, [], "Loading…");
    const response = await fetch(`/api/districts/${encodeURIComponent(region)}`);
    const districts = await response.json();
    fillSelect(districtSelect, districts, "Select your district");
    districtSelect.disabled = false;
  } catch (err) {
    fillSelect(districtSelect, [], "Could not load districts");
    console.error("Failed to load districts:", err);
  }
}

// Wire the region select so choosing one repopulates the district select.
regionSelect.addEventListener("change", (e) => loadDistricts(e.target.value));

// 3. Final safety check before submit: make sure nothing required is empty.
const portalForm = document.getElementById("portal-form");
portalForm.addEventListener("submit", (e) => {
  const requiredEls = portalForm.querySelectorAll("[required]");
  for (const el of requiredEls) {
    if (!el.value || (el.type === "file" && el.files.length === 0)) {
      e.preventDefault();
      alert("Please fill in every field before submitting.");
      el.focus();
      return;
    }
  }
});

// Kick things off as soon as the page is ready.
loadRegions();
