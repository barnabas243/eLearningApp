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


const profileMessage = document.querySelector('#profile-message');
// Function to handle blur event on span elements
function handleSpanBlur(event) {
    // Get the field name from the id of the span

  
    const field = this.id;

    // Get the new value of the span
    const newValue = this.innerText.trim();

    // Get the initial value of the field
    const oldValue = initialFieldValues[field];
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    
    // Send a PUT request to update the field
    fetch(`/profile/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ [field]: newValue })
    })
        .then(response => {
            // Check if the response is OK
            if (!response.ok) {
                response.json().then(error => {
                    console.error('Error:', error);

                    // Rollback the span value to the initial value
                    this.innerText = oldValue;

                    // Display the error message in the profile message span
                    profileMessage.textContent = error;

                })
            }
        })
        .catch(error => {
            // Log the error to the console
            console.error('Error:', error);

            // Rollback the span value to the initial value
            this.innerText = oldValue;

            // Display the error message in the profile message span
            profileMessage.textContent = error;
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



const updatePassForm = document.querySelector('#updatePassForm') || null;
const changePassConfirmBtn =
  document.querySelector('#changePassConfirmBtn') || null;

  
const toggleOldPassword = document.querySelector('#toggleOldPassword') || null;
const togglePassword = document.querySelector('#togglePassword') || null;
const toggleConfirmPassword =
  document.querySelector('#toggleConfirmPassword') || null;

const password = document.querySelector('#password') || null;
const password_confirm = document.querySelector('#password_confirm') || null;
const oldPassword = document.querySelector('#oldPassword') || null;

const pass_regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\w\d\W]{8,}$/;


function clearInputValidClasses() {
  const inputs = updatePassForm.querySelectorAll('input')

  inputs.forEach((input) => {
    input.classList.remove("is-invalid","is-valid")
  })
}
/**
 * updatePassForm submit event listener to send a fetch request that checks the validity of the old password and new passwords.
 * Error handling is done when either of the input is determined as invalid from the server 
 */
if (updatePassForm) {
  changePassConfirmBtn.disabled = true;

  updatePassForm.addEventListener('submit', (e) => {
    e.preventDefault();
        
    changePassConfirmBtn.disabled = true;

    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;


    const changePassSpinner = document.querySelector('#changePassSpinner');
    const ChangePassText = document.querySelector('#ChangePassText');

    changePassSpinner.classList.remove('visually-hidden');
    ChangePassText.textContent = 'updating...';

    const oldPasswordValue = e.target.oldPassword.value;
    const passwordValue = e.target.password.value;
    const password_confirmValue = e.target.password_confirm.value;

    const newPasswordFeedback = document.querySelector('#newPasswordFeedback');

    fetch('/auth/change-password/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify({
        old_password: oldPasswordValue,
        new_password: passwordValue,
        confirm_password: password_confirmValue,
      }),
    })
      .then((res) => {
        if (res.status === 200) {
          window.location.assign('https://localhost/profile');
        } else if (res.status === 400) {
            res.json().then((data) => {
                // Display error messages for new_password and confirm_password
                console.log("data: ", data)
                
                Object.keys(data).forEach((key) => {
                    console.log("ERROR 400 data[key]: ", data[key])
                    const errorMessage = data[key]; // Get the error message
                    
                    console.log("errorMessage:", errorMessage);
                    console.log("Type: ",typeof(data[key])) // sting
                    console.log("Length:", errorMessage.length);
                    if (errorMessage.trim() === "New password cannot be the same as old password.") {

                        console.log("why did this fail?")
                        newPasswordFeedback.textContent = errorMessage;

                        password.classList.add('is-invalid')
                        password.classList.remove('is-valid')
                    }
                    if (errorMessage.trim() === "Passwords do not match.") {

                        password_confirm.classList.add('is-invalid')
                        password_confirm.classList.remove('is-valid')
                    }
                });
            })


            oldPassword.classList.add('is-valid');
            oldPassword.classList.remove('is-invalid');

        } else if (res.status === 422) {

            oldPassword.classList.add('is-invalid');

        } else {
            res.json().then((data) => {
                // Display error messages for each field
                Object.keys(data).forEach((key) => {
                  console.log("data[key]: ",data[key])
                  const errorMessage = data[key][0];
                  // Display error message for the corresponding field

                  // You can handle other fields similarly if needed
                });
            })

        }
      })
      .catch((error) => {
        console.error(error);
      })
      .finally(() => {
          changePassSpinner.classList.add('visually-hidden');
          ChangePassText.textContent = 'Change Password';

          changePassConfirmBtn.disabled = false;
      });
  });
}

/**
 * password input event listener to check whether password conforms to the password regex
 * includes the visibility toggle
 * includes checking of whether password_confirm matches the password.
 */
if (password) {
    togglePassword.addEventListener('click', function () {
      // toggle the type attribute
      const type =
        password.getAttribute('type') === 'password' ? 'text' : 'password';
      password.setAttribute('type', type);
      // toggle the eye icon
      this.classList.toggle('fa-eye');
      this.classList.toggle('fa-eye-slash');
    });
    password.addEventListener('input', (e) => {
      if (pass_regex.test(e.target.value)) {
        e.target.classList.remove('is-invalid');
        e.target.classList.add('is-valid');
      } else {
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
      }
      if (
        password_confirm.value !== e.target.value &&
        password_confirm.classList.contains('is-valid')
      ) {
        password_confirm.classList.add('is-invalid');
        password_confirm.classList.remove('is-valid');
        if (changePassConfirmBtn) changePassConfirmBtn.disabled = true;
      } else if (
        password_confirm.value === e.target.value &&
        password_confirm.classList.contains('is-invalid')
      ) {
        password_confirm.classList.remove('is-invalid');
        password_confirm.classList.add('is-valid');
        if (changePassConfirmBtn) changePassConfirmBtn.disabled = false;
      }
    });
  }
  /**
   * password confirm input event listener to check whether password conforms to the password regex
   * includes the visibility toggle
   * includes checking of whether password matches the confirm_password.
   */
  if (password_confirm) {
    toggleConfirmPassword.addEventListener('click', function () {
      // toggle the type attribute
      const type =
        password_confirm.getAttribute('type') === 'password'
          ? 'text'
          : 'password';
      password_confirm.setAttribute('type', type);
      // toggle the eye icon
      this.classList.toggle('fa-eye');
      this.classList.toggle('fa-eye-slash');
    });
    password_confirm.addEventListener('input', (e) => {
      if (pass_regex.test(e.target.value) && e.target.value === password.value) {
        e.target.classList.remove('is-invalid');
        e.target.classList.add('is-valid');
        if (changePassConfirmBtn) changePassConfirmBtn.disabled = false;
      } else {
        e.target.classList.add('is-invalid');
        e.target.classList.remove('is-valid');
        if (changePassConfirmBtn) changePassConfirmBtn.disabled = true;
      }
    });
  }
  /**
   * the profile page old password visibility toggle
   */
  if (oldPassword) {
    toggleOldPassword.addEventListener('click', function () {
      // toggle the type attribute
      const type =
        oldPassword.getAttribute('type') === 'password' ? 'text' : 'password';
      oldPassword.setAttribute('type', type);
      // toggle the eye icon
      this.classList.toggle('fa-eye');
      this.classList.toggle('fa-eye-slash');
    });
  }
  