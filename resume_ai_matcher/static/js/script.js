document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('uploadForm');
    const submitBtn = document.getElementById('submitBtn');
    const spinner = document.getElementById('loadingSpinner');

    if(form) {
        form.addEventListener('submit', function(e) {
            // Check HTML5 validity
            if (form.checkValidity()) {
                submitBtn.disabled = true;
                const btnContent = Array.from(submitBtn.childNodes).find(node => node.nodeType === 3);
                if(btnContent) {
                    btnContent.textContent = 'Evaluating Resumes... ';
                }
                spinner.classList.remove('d-none');
                
                // Submit programmatically since btn is disabled (otherwise logic fails in some browsers)
                form.submit();
            }
        });
    }
});
