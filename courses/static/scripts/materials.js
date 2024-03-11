if (materialsScriptLoaded === undefined) {
    console.log("loaded")

    let fileInput = document.querySelector('#id_material');

    if (fileInput) {
        fileInput.addEventListener('change', function () {
            // Iterate over selected files
            for (const file of fileInput.files) {
                // Check the file type
                if (file.type === 'application/pdf' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document') {
                    // For PDF and DOCX files, create a downloadable link
                    const downloadLink = document.createElement('a');
                    downloadLink.textContent = file.name;
                    downloadLink.href = URL.createObjectURL(file);
                    downloadLink.download = file.name;

                    // Create a list item to contain the download link and delete button
                    const listItem = document.createElement('li');
                    listItem.appendChild(downloadLink);

                    // Append the list item to the file preview container
                    filePreview.appendChild(listItem);
                } else if (file.type.startsWith('image/')) {
                    // For image files, create an image preview
                    const imagePreview = document.createElement('img');
                    imagePreview.src = URL.createObjectURL(file);
                    imagePreview.alt = file.name;

                    // Create a list item to contain the image preview
                    const listItem = document.createElement('li');
                    listItem.appendChild(imagePreview);

                    // Append the list item to the file preview container
                    filePreview.appendChild(listItem);
                }
            }
        });
    }

    function showLoadingIndicator(btn_type) {
        let loadingIndicator;
        if (btn_type === "material") {
            document.querySelector('#uploadMaterialModalCloseBtn').click()
            loadingIndicator = document.querySelector('#materialLoadingIndicator')
        }
        else if (btn_type === "assignment") {
            document.querySelector('#uploadAssignmentModalCloseBtn').click()
            loadingIndicator = document.querySelector('#assignmentLoadingIndicator')
        }


        loadingIndicator.classList.remove('visually-hidden')
    }

    const saveBtn = document.getElementById('assignmentUploadBtn');
    // Add event listener to save button
    if (saveBtn) {
        saveBtn.addEventListener('click', function () {
            // Get the CKEditor instance
            const editor = CKEDITOR.instances.id_instructions;

            // Get the CKEditor content
            let content = editor.getData();

            // Set the content to a hidden input field
            document.getElementById('id_instructions').value = content;
        });
    }
}