document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("jobSeekerForm");
  const resumeInput = document.getElementById("resume");
  const resumeUploadStatus = document.getElementById("resumeUploadStatus");
  const resumeUploadFilename = document.getElementById("resumeUploadFilename");
  const submitBtn = document.getElementById("jobSeekerSubmit");
  const spinner = document.getElementById("jobSeekerSpinner");

  if (!form || !resumeInput) return;

  resumeInput.addEventListener("change", () => {
    const file = resumeInput.files && resumeInput.files[0];
    if (!file) {
      if (resumeUploadStatus) resumeUploadStatus.classList.add("d-none");
      if (resumeUploadFilename) resumeUploadFilename.textContent = "";
      return;
    }

    if (resumeUploadStatus) resumeUploadStatus.classList.remove("d-none");
    if (resumeUploadFilename) resumeUploadFilename.textContent = `Selected: ${file.name}`;
  });

  form.addEventListener("submit", () => {
    if (spinner) spinner.classList.remove("d-none");
    if (submitBtn) submitBtn.disabled = true;
  });
});

