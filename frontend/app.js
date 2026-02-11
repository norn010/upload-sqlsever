const uploadForm = document.getElementById("upload-form");
const submitBtn = document.getElementById("submit-btn");
const statusCard = document.getElementById("status-card");
const errorsCard = document.getElementById("errors-card");
const summaryEl = document.getElementById("summary");
const errorsBody = document.querySelector("#errors-table tbody");

const setBusy = (busy) => {
  submitBtn.disabled = busy;
  submitBtn.textContent = busy ? "Importing..." : "Upload and Import";
};

const showSummary = (payload) => {
  statusCard.classList.remove("hidden");
  summaryEl.textContent = JSON.stringify(
    {
      job_id: payload.job_id,
      status: payload.status,
      filename: payload.filename,
      total_rows: payload.total_rows,
      imported_rows: payload.imported_rows,
      failed_rows: payload.failed_rows,
      message: payload.message,
    },
    null,
    2
  );
};

const showErrors = (errors) => {
  errorsBody.innerHTML = "";
  if (!errors || errors.length === 0) {
    errorsCard.classList.add("hidden");
    return;
  }

  errorsCard.classList.remove("hidden");
  for (const item of errors) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${item.row_number}</td>
      <td>${item.column_name || "-"}</td>
      <td>${item.error_message}</td>
    `;
    errorsBody.appendChild(row);
  }
};

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const fileInput = document.getElementById("excel-file");
  const file = fileInput.files[0];
  if (!file) {
    alert("Please choose an Excel file.");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  setBusy(true);
  try {
    const response = await fetch("/api/imports/upload", {
      method: "POST",
      body: formData,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Upload failed.");
    }

    showSummary(payload);
    showErrors(payload.errors || []);
  } catch (error) {
    statusCard.classList.remove("hidden");
    summaryEl.textContent = error.message;
    errorsCard.classList.add("hidden");
  } finally {
    setBusy(false);
  }
});
