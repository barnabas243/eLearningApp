// Get the form element and add an event listener for form submission
const form = document.querySelector('form');
form.addEventListener('submit', (event) => {
    event.preventDefault(); // Prevent the default form submission behavior

    // add loading indicator on submit button
    const submitButton = form.querySelector('button[type="submit"]');
    const loginSpinner = document.querySelector('#loginSpinner');
    const loginBtnText = document.querySelector('#loginBtnText');

    submitButton.disabled = true
    loginSpinner.classList.remove('visually-hidden');
    loginBtnText.textContent = 'Logging in...';
    
    // Serialize form data into JSON format
    const formData = new FormData(form);
    const jsonData = {};
    formData.forEach((value, key) => {jsonData[key] = value});

    // Make a POST request using fetch()
    fetch('/auth/login/', {
        method: 'POST',
        body: JSON.stringify(jsonData), // Convert form data to JSON
        headers: {
            'Content-Type': 'application/json', // Specify content type as JSON
            'X-CSRFToken': '{{ csrf_token }}' // Include the CSRF token
        }
    })
    .then(response => {
        if (response.ok) {
            // Parse the query string to retrieve the "next" parameter
            const queryString = window.location.search;
            const urlParams = new URLSearchParams(queryString);
            const nextUrl = urlParams.get("next");
            
            // Redirect to the dashboard or another page upon successful login
            if (nextUrl) {
                window.location.href = nextUrl;
            } else {
                window.location.href = '/dashboard/';
            }
        } else {
            // Handle errors and display error messages
            response.json().then(data => {
                if (response.status === 400) {
                    // Handle 400 Bad Request errors
                    if(data.error === "required") {
                        console.error('Error:', data.error);
                        const usernameErrorMessage = document.getElementById('username-error-message')
                        usernameErrorMessage.textContent = "Username cannot be empty";
    
                        const usernameInput = document.getElementById('id_username');
                        usernameInput.classList.add('is-invalid');

                        const passwordErrorMessage = document.getElementById('username-error-message')
                        passwordErrorMessage.textContent = "Password cannot be empty";
    
                        const passwordInput = document.getElementById('id_password');
                        passwordInput.classList.add('is-invalid');
                    }
    
                } else if (response.status === 401) {
                    // Handle 401 Unauthorized errors
                    if (data.error === "Invalid username or password.") {
                        // Display error message for invalid credentials
                        console.error('Error:', data.error);
                        const usernameErrorMessage = document.getElementById('username-error-message')
                        usernameErrorMessage.textContent = data.error;
    
                        const usernameInput = document.getElementById('id_username');
                        usernameInput.classList.add('is-invalid');

                    } else if (data.error === "User account is disabled.") {
                        // Display error message for disabled account
                        console.error('Error:', data.error);
                        // Handle disabled account error
                    } else {
                        // Handle other 401 errors
                        console.error('Error:', data.error);
                        // Handle other types of errors
                    }
                } else {
                    // Handle other HTTP status codes
                    console.error('Error:', data.error);
                    // Handle other types of errors
                }
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
    })
    .finally(() => {
        // Re-enable submit button and hide spinner after request is completed
        submitButton.disabled = false;
        loginSpinner.classList.add('visually-hidden');
        loginBtnText.textContent = 'Login';
    });
    
});
