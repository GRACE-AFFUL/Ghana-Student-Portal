// details.js — updates a student's admission status asynchronously.
// When the select changes, we POST the new value to the server and update
// the badge in place, without reloading the page.

const statusSelect = document.getElementById("status-select");
const statusBadge = document.getElementById("status-badge");
const statusMsg = document.getElementById("status-msg");

statusSelect.addEventListener("change", async (e) => {
  const studentId = e.target.dataset.id;   // set via data-id in the template
  const newStatus = e.target.value;

  statusMsg.textContent = "Saving…";
  statusMsg.className = "status-msg";

  try {
    const response = await fetch(`/api/student/${studentId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus }),
    });
    const data = await response.json();

    if (data.ok) {
      // Update the badge text and its colour class to match the new status.
      statusBadge.textContent = data.status;
      statusBadge.className = "badge badge--" + data.status.toLowerCase();
      statusMsg.textContent = "Saved.";
      statusMsg.classList.add("ok");
    } else {
      statusMsg.textContent = data.error || "Could not save.";
      statusMsg.classList.add("err");
    }
  } catch (err) {
    statusMsg.textContent = "Network error. Try again.";
    statusMsg.classList.add("err");
    console.error(err);
  }
});
