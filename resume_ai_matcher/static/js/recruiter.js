document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("recruiterForm");
  const input = document.getElementById("resumes");
  const status = document.getElementById("recruiterUploadStatus");
  const fileText = document.getElementById("recruiterUploadFilename");
  const submitBtn = document.getElementById("recruiterSubmit");
  const spinner = document.getElementById("recruiterSpinner");

  if (!form || !input) return;

  input.addEventListener("change", () => {
    const files = input.files || [];
    if (!files.length) {
      if (status) status.classList.add("d-none");
      if (fileText) fileText.textContent = "";
      return;
    }

    if (status) status.classList.remove("d-none");
    if (fileText) fileText.textContent = `${files.length} PDF(s) selected`;
  });

  form.addEventListener("submit", () => {
    if (spinner) spinner.classList.remove("d-none");
    if (submitBtn) submitBtn.disabled = true;
  });
});

