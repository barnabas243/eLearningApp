// ===============================================
// Profile Form Handling
// ===============================================

// Function to get the initial values of profile fields
function getInitialFieldValues() {
    // Initialize an object to store initial field values
    const initialValues = {};
    
    // Define an array of field names
    const fields = ['username', 'first_name', 'last_name', 'email'];
    
    // Iterate over each field and retrieve its initial value
    fields.forEach(field => {
        initialValues[field] = document.getElementById(field).innerText.trim();
    });
    
    // Return the object containing initial field values
    return initialValues;
}

// Function to handle file input change event
function handleFileInputChange(event) {
    // Get the profile preview element
    const preview = document.getElementById('profilePreview');
    
    // Get the selected file
    const file = this.files[0];
    
    // Create a file reader object
    const reader = new FileReader();

    // Define the onload event handler for the file reader
    reader.onload = function (e) {
        preview.src = e.target.result;
    };

    // Read the selected file as a data URL
    reader.readAsDataURL(file);
}

// Function to toggle contentEditable on span click
function toggleContentEditable() {
    // Get the field name from the data attribute of the clicked icon
    const field = this.dataset.field;
    
    // Get the corresponding span element
    const span = document.getElementById(field);
    
    // Toggle the contentEditable property of the span
    span.contentEditable = !span.isContentEditable;
    
    // Focus on the span element
    span.focus();
}

// Function to handle keydown event on span elements
function handleSpanKeyDown(event) {
    // Check if the Enter key is pressed
    if (event.key === 'Enter') {
        // Prevent the default Enter key behavior
        event.preventDefault();
        
        // Blur the span to lose focus
        this.blur();
    }
}

// Function to handle blur event on span elements
function handleSpanBlur(event) {
    // Get the field name from the id of the span
    const field = this.id;
    
    // Get the new value of the span
    const newValue = this.innerText.trim();
    
    // Get the initial value of the field
    const oldValue = initialFieldValues[field];

    // Send a PUT request to update the field
    fetch(`/profile/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': '{{ csrf_token }}'
        },
        body: JSON.stringify({ [field]: newValue })
    })
    .then(response => {
        // Check if the response is OK
        if (!response.ok) {
            // Throw an error if the response is not OK
            throw new Error(`Failed to update ${field}`);
        }
    })
    .catch(error => {
        // Log the error to the console
        console.error('Error:', error);
        
        // Rollback the span value to the initial value
        this.innerText = oldValue;
        
        // Display the error message in the profile message span
        profileMessageSpan.textContent = error;
    });
}

// Get the initial values of profile fields
const initialFieldValues = getInitialFieldValues();

// Add event listener for file input change
document.getElementById('id_photo').addEventListener('change', handleFileInputChange);

// Add event listeners for edit icons
document.querySelectorAll('.edit-icon').forEach(icon => {
    icon.addEventListener('click', toggleContentEditable);
});

// Add event listeners for span elements
document.querySelectorAll('.card-text span').forEach(span => {
    span.addEventListener('keydown', handleSpanKeyDown);
    span.addEventListener('blur', handleSpanBlur);
});
