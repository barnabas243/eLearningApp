// ===============================================
// Input Fields
// ===============================================

// Define input fields
const emailInput = document.getElementById('id_email');
const firstNameInput = document.getElementById('id_first_name');
const lastNameInput = document.getElementById('id_last_name');
const usernameInput = document.getElementById('id_username');
const dateOfBirthInput = document.getElementById('id_date_of_birth');
const password1Input = document.getElementById('id_password1');
const password2Input = document.getElementById('id_password2');


// ===============================================
// Validation Functions
// ===============================================

// Function to check if email is valid
function validateEmail() {
    if (emailInput.value.trim() === '' || /\S+@\S+\.\S+/.test(emailInput.value)) {
        emailInput.classList.add('is-valid');
        emailInput.classList.remove('is-invalid');
        
    } else {
        emailInput.classList.add('is-invalid');
        emailInput.classList.remove('is-valid');
    }
}

// Function to check if first name and last name are not empty
function validateName() {
    if (firstNameInput.value.trim() === '') {
        firstNameInput.classList.add('is-invalid');
        firstNameInput.classList.remove('is-valid');

    } else {
        firstNameInput.classList.add('is-valid');
        firstNameInput.classList.remove('is-invalid');
    }

    if (lastNameInput.value.trim() === '') {
        lastNameInput.classList.add('is-invalid');
        lastNameInput.classList.remove('is-valid');
    } else {
        lastNameInput.classList.add('is-valid');
        lastNameInput.classList.remove('is-invalid');
    }
}

// // Function to check if password meets requirements and update help text
// function validatePasswordRequirements() {
//     const usernameSimilarity = calculateSimilarity(usernameInput.value, password1Input.value);
//     const firstNameSimilarity = calculateSimilarity(firstNameInput.value, password1Input.value);
//     const lastNameSimilarity = calculateSimilarity(lastNameInput.value, password1Input.value);
//     const emailSimilarity = calculateSimilarity(emailInput.value, password1Input.value);

//     const maxSimilarity = Math.max(usernameSimilarity, firstNameSimilarity, lastNameSimilarity, emailSimilarity);

//     const commonPasswordsPattern = /^(?:123(?:456(?:7(?:89(?:0)?)?)?|45|456(?:78)?)|password(?:1)?|qwerty(?:123)?|abc123|111111|iloveyou|1q2w3e4r|000000|zaq12wsx|dragon|sunshine|princess|letmein|654321|monkey|27653|1qaz2wsx|123321|qwertyuiop|superman|asdfghjkl)$/i;
    
//     const requirements = {
//         0: maxSimilarity < 0.4, // similarity between passwords and username,firstname,lastname and email to be less than 0.4
//         1: password1Input.value.length >= 8, // Check if password has at least 8 characters
//         2: !commonPasswordsPattern.test(password1Input.value), // Check if password is not one of the common passwords
//         3: !/^\d+$/.test(password1Input.value) // Check if password is not entirely numeric
//     };

//     // Update color of each requirement based on validity
//     password1Requirements.forEach(function (requirementElement) {
//         const requirementKey = [...password1Requirements].indexOf(requirementElement)
//         if (requirements[requirementKey]) {
//             requirementElement.classList.remove('invalid');
//             requirementElement.classList.add('valid');
//         } else {
//             requirementElement.classList.remove('valid');
//             requirementElement.classList.add('invalid');
//         }
//     });

//     // Check if all requirements are fulfilled
//     const allRequirementsFulfilled = Object.values(requirements).every(value => value);
// }

// // Function to calculate Levenshtein distance between two strings
// function levenshteinDistance(str1, str2) {
//     const len1 = str1.length;
//     const len2 = str2.length;

//     const dp = Array.from(Array(len1 + 1), () => Array(len2 + 1).fill(0));

//     for (let i = 0; i <= len1; i++) {
//         dp[i][0] = i;
//     }

//     for (let j = 0; j <= len2; j++) {
//         dp[0][j] = j;
//     }

//     for (let i = 1; i <= len1; i++) {
//         for (let j = 1; j <= len2; j++) {
//             const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
//             dp[i][j] = Math.min(
//                 dp[i - 1][j] + 1, // deletion
//                 dp[i][j - 1] + 1, // insertion
//                 dp[i - 1][j - 1] + cost // substitution
//             );
//         }
//     }

//     return dp[len1][len2];
// }

// Function to calculate similarity ratio between two strings
function calculateSimilarity(str1, str2) {
    const distance = levenshteinDistance(str1.toLowerCase(), str2.toLowerCase());
    const maxLength = Math.max(str1.length, str2.length);
    const similarityRatio = (maxLength - distance) / maxLength;
    return similarityRatio;
}

// Function to hide help text for confirm password if it matches first password
function validateConfirmPassword() {
    if (password2Input.value === password1Input.value) {
        password2Input.classList.add('is-valid')
        password2Input.classList.remove('is-invalid')
    } else {
        password2Input.classList.add('is-invalid')
        password2Input.classList.remove('is-valid')
    }
}

// Function to validate username input and hide/show help text
function validateUsername() {
    const isValid = /^[\w.@+-]{8,150}/.test(usernameInput.value);
    if(isValid) {
        usernameInput.classList.add('is-valid');
        usernameInput.classList.remove('is-invalid');
    }
    else{  
        usernameInput.classList.add('is-invalid')
        usernameInput.classList.remove('is-valid')
    }
}

function validateDateOfBirth() {
    const dateOfBirthInput = document.getElementById('id_date_of_birth');
    const inputValue = dateOfBirthInput.value;
    const minDate = new Date(dateOfBirthInput.min);
    const maxDate = new Date(dateOfBirthInput.max);
    const inputDate = new Date(inputValue);
    
    if (inputDate >= minDate && inputDate <= maxDate) {
        dateOfBirthInput.classList.add('is-valid');
        dateOfBirthInput.classList.remove('is-invalid');
    } else {
        dateOfBirthInput.classList.add('is-invalid');
        dateOfBirthInput.classList.remove('is-valid');
    }
}

// ===============================================
// Event Listeners
// ===============================================

// Event listeners for input fields
emailInput.addEventListener('input',validateEmail);
usernameInput.addEventListener('input', validateUsername);
lastNameInput.addEventListener('input', validateName);
firstNameInput.addEventListener('input', validateName);
dateOfBirthInput.addEventListener('input', validateDateOfBirth);
password2Input.addEventListener('input', validateConfirmPassword);

const form = document.querySelector('form');

form.addEventListener('submit', (event) => {
    event.preventDefault();
    
    // Add loading indicator on submit button
    console.log("Clicked on register");
    const submitButton = form.querySelector('button[type="submit"]');
    const registerSpinner = document.querySelector('#registerSpinner');
    const registerBtnText = document.querySelector('#registerBtnText');

    submitButton.disabled = true;
    registerSpinner.classList.remove('visually-hidden');
    registerBtnText.textContent = 'Registering...';
    
    const formData = new FormData(form);

    fetch('/auth/register/', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (response.ok) {
            // Registration successful, redirect or show a success message
            window.location.href = '/dashboard/';
        } else {
            // Registration failed, handle errors
            return response.json();
        }
    })
    .then(data => {
        // Display error messages to the user
        for (const key in data) {
            if (Object.hasOwnProperty.call(data, key)) {
                const errorMessage = document.getElementById(`${key}-error`);
                if (errorMessage) {
                    errorMessage.textContent = data[key][0];
                    document.getElementById(`id_${key}`).classList.add('is-invalid')
                    document.getElementById(`id_${key}`).classList.remove('is-valid')
                }
            }
        }
        console.error('Registration failed:', data);
        // You can display error messages to the user here
    })
    .catch(error => {
        // Handle network errors
        console.error('Error:', error);
    })
    .finally(() => {
        // Re-enable submit button and hide spinner after request is completed
        submitButton.disabled = false;
        registerSpinner.classList.add('visually-hidden');
        registerBtnText.textContent = 'Register';
    });
});
