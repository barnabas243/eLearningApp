document.addEventListener('DOMContentLoaded', function () {
    const usernameInput = document.getElementById('id_username');
    const usernameHelpText = document.getElementById('id_username_helptext');
    const password1Input = document.getElementById('id_password1');
    const password1HelpText = document.getElementById('id_password1_helptext');
    const password2Input = document.getElementById('id_password2');
    const password2HelpText = document.getElementById('id_password2_helptext');

    // Function to check if password meets requirements and update help text
    function validatePasswordRequirements() {
        const requirements = {
            similarToPersonal: /[a-zA-Z]/.test(password1Input.value), // Check if password contains at least one letter
            atLeast8Chars: password1Input.value.length >= 8, // Check if password has at least 8 characters
            notCommon: !/(password|123456|qwerty)/i.test(password1Input.value), // Check if password is not one of the common passwords
            notEntirelyNumeric: !/^\d+$/.test(password1Input.value) // Check if password is not entirely numeric
        };

        // Update color of each requirement based on validity
        Object.keys(requirements).forEach(key => {
            const requirementElement = document.getElementById(key);
            if (requirements[key]) {
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

    // Function to hide help text for confirm password if it matches first password
    function validateConfirmPassword() {
        if (password2Input.value === password1Input.value) {
            password2HelpText.style.display = 'none';
        } else {
            password2HelpText.style.display = 'block';
        }
    }

    if (password1Input && password2Input) {
        password1Input.addEventListener('input', validatePasswordRequirements);
        password2Input.addEventListener('input', validateConfirmPassword);
        // Event listeners for input fields
        usernameInput.addEventListener('input', function () {
            if (usernameInput.validity.valid) {
                usernameHelpText.style.display = 'none';
            } else {
                usernameHelpText.style.display = 'block';
            }
        });
    }
});
