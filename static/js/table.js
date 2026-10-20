// Client-side filters for the students index table.
const searchInput = document.getElementById("table-search");
const statusFilter = document.getElementById("status-filter");
const genderFilter = document.getElementById("gender-filter");
const aggregateFilter = document.getElementById("aggregate-filter");
const filterButton = document.getElementById("table-filter-button");
const table = document.getElementById("students-table");

if (searchInput && statusFilter && genderFilter && aggregateFilter && filterButton && table) {
  const rows = table.querySelectorAll("tbody tr");

  const filterRows = () => {
    const name = searchInput.value.trim().toLowerCase();
    const status = statusFilter.value.toLowerCase();
    const gender = genderFilter.value.toLowerCase();
    const aggregate = aggregateFilter.value.trim();

    rows.forEach((row) => {
      const matchesName = row.dataset.name.toLowerCase().includes(name);
      const matchesStatus = !status || row.dataset.status.toLowerCase() === status;
      const matchesGender = !gender || row.dataset.gender.toLowerCase() === gender;
      const matchesAggregate = !aggregate || row.dataset.aggregate === aggregate;

      row.style.display = matchesName && matchesStatus && matchesGender && matchesAggregate
        ? ""
        : "none";
    });
  };

  filterButton.addEventListener("click", filterRows);
  searchInput.addEventListener("input", filterRows);
  statusFilter.addEventListener("change", filterRows);
  genderFilter.addEventListener("change", filterRows);
  aggregateFilter.addEventListener("input", filterRows);
}
