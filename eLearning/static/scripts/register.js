// ===============================================
// Input Fields
// ===============================================

// Define input fields
const emailInput = document.getElementById('id_email');
const firstNameInput = document.getElementById('id_first_name');
const lastNameInput = document.getElementById('id_last_name');
const usernameInput = document.getElementById('id_username');
const password1Input = document.getElementById('id_password1');
const password2Input = document.getElementById('id_password2');

// Define help text elements
const usernameHelpText = document.getElementById('id_username_helptext');
const password1HelpText = document.getElementById('id_password1_helptext');
const password2HelpText = document.getElementById('id_password2_helptext');
const password1Requirements = document.querySelectorAll('#id_password1_helptext li');

// ===============================================
// Validation Functions
// ===============================================

// Function to check if email is valid
function validateEmail() {
    if (emailInput.value.trim() === '' || /\S+@\S+\.\S+/.test(emailInput.value)) {
        emailInput.classList.remove('is-invalid');
    } else {
        emailInput.classList.add('is-invalid');
    }
}

// Function to check if first name and last name are not empty
function validateName() {
    if (firstNameInput.value.trim() === '') {
        firstNameInput.classList.add('is-invalid');
    } else {
        firstNameInput.classList.remove('is-invalid');
    }

    if (lastNameInput.value.trim() === '') {
        lastNameInput.classList.add('is-invalid');
    } else {
        lastNameInput.classList.remove('is-invalid');
    }
}

// Function to check if password meets requirements and update help text
function validatePasswordRequirements() {
    const usernameSimilarity = calculateSimilarity(usernameInput.value, password1Input.value);
    const firstNameSimilarity = calculateSimilarity(firstNameInput.value, password1Input.value);
    const lastNameSimilarity = calculateSimilarity(lastNameInput.value, password1Input.value);
    const emailSimilarity = calculateSimilarity(emailInput.value, password1Input.value);

    const maxSimilarity = Math.max(usernameSimilarity, firstNameSimilarity, lastNameSimilarity, emailSimilarity);

    const commonPasswordsPattern = /^(?:123(?:456(?:7(?:89(?:0)?)?)?|45|456(?:78)?)|password(?:1)?|qwerty(?:123)?|abc123|111111|iloveyou|1q2w3e4r|000000|zaq12wsx|dragon|sunshine|princess|letmein|654321|monkey|27653|1qaz2wsx|123321|qwertyuiop|superman|asdfghjkl)$/i;
    
    const requirements = {
        0: maxSimilarity < 0.4, // similarity between passwords and username,firstname,lastname and email to be less than 0.4
        1: password1Input.value.length >= 8, // Check if password has at least 8 characters
        2: !commonPasswordsPattern.test(password1Input.value), // Check if password is not one of the common passwords
        3: !/^\d+$/.test(password1Input.value) // Check if password is not entirely numeric
    };

    // Update color of each requirement based on validity
    password1Requirements.forEach(function (requirementElement) {
        const requirementKey = [...password1Requirements].indexOf(requirementElement)
        if (requirements[requirementKey]) {
            requirementElement.classList.remove('invalid');
            requirementElement.classList.add('valid');
        } else {
            requirementElement.classList.remove('valid');
            requirementElement.classList.add('invalid');
        }
    });

    // Check if all requirements are fulfilled
    const allRequirementsFulfilled = Object.values(requirements).every(value => value);
    if (allRequirementsFulfilled) {
        password1HelpText.style.display = 'none';
    } else {
        password1HelpText.style.display = 'block';
    }
}

// Function to calculate Levenshtein distance between two strings
function levenshteinDistance(str1, str2) {
    const len1 = str1.length;
    const len2 = str2.length;

    const dp = Array.from(Array(len1 + 1), () => Array(len2 + 1).fill(0));

    for (let i = 0; i <= len1; i++) {
        dp[i][0] = i;
    }

    for (let j = 0; j <= len2; j++) {
        dp[0][j] = j;
    }

    for (let i = 1; i <= len1; i++) {
        for (let j = 1; j <= len2; j++) {
            const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
            dp[i][j] = Math.min(
                dp[i - 1][j] + 1, // deletion
                dp[i][j - 1] + 1, // insertion
                dp[i - 1][j - 1] + cost // substitution
            );
        }
    }

    return dp[len1][len2];
}

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
        password2HelpText.style.display = 'none';
    } else {
        password2HelpText.style.display = 'block';
    }
}

// Function to validate username input and hide/show help text
function validateUsername() {
    const isValid = /^[\w.@+-]{8,50}/.test(usernameInput.value);
    usernameHelpText.style.display = isValid ? 'none' : 'block';
}

// ===============================================
// Event Listeners
// ===============================================

// Event listeners for input fields
usernameInput.addEventListener('input', validateUsername);
password1Input.addEventListener('input', validatePasswordRequirements);
password2Input.addEventListener('input', validateConfirmPassword);