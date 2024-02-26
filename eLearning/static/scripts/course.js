let materialsScriptLoaded;
window.onload = function () {

    // Get the course tabs (for teachers only)
    const courseTabs = document.getElementById('courseTabs');
    if (courseTabs) {
        // Add event listener for tab clicks
        courseTabs.addEventListener('click', function (event) {
            // Get the clicked tab's id
            const clickedTabId = event.target.id;

            // Save the id of the clicked tab to sessionStorage
            sessionStorage.setItem('activeTabId', clickedTabId);
        });

        // Check if there's a saved active tab id in sessionStorage

        const activeTabId = sessionStorage.getItem('activeTabId');
        if (activeTabId) {
            // Find the tab button with the saved id and trigger a click event on it
            const tabButton = document.getElementById(activeTabId);
            if (tabButton) {
                tabButton.click();
            } else {
                courseTabs.querySelector('button').click();
            }
        } else {
            courseTabs.querySelector('button').click();
        }
    }


    // Get the current URL
    const url = window.location.href;

    // Parse the URL to get query parameters
    const params = new URLSearchParams(url.split('?')[1]);

    // Get the value of the 'week' parameter
    const weekValue = params.get('week');

    // Check if 'weekValue' is null (meaning 'week' parameter doesn't exist) or not a number
    if (weekValue === null || isNaN(weekValue)) {
        console.log("Week parameter is not a valid number");

        // get the 1st week by default
        document.querySelector('a[data-week="1"]').click();
    } else {
        // Convert weekValue to integer
        const weekNumber = parseInt(weekValue);

        // Select the link element corresponding to weekNumber
        const weekLink = document.querySelector(`a[data-week="${weekNumber}"]`);

        // Check if the link element exists before triggering click event
        if (weekLink) {
            // Trigger click event on the link corresponding to weekNumber
            weekLink.click();
        } else {
            console.log(`Week ${weekNumber} link not found`);
            // Default action if week link is not found
            document.querySelector('a[data-week="1"]').click();
        }
    }


    // Get all star rating inputs
    const teacher_rating = document.querySelector('#teacher_rating_stars');
    const course_rating = document.querySelector('#course_rating_stars')

    if (teacher_rating && course_rating) {
        const teacher_star_inputs = teacher_rating.querySelectorAll('.star-rating input[type="checkbox"]');
        const course_star_inputs = course_rating.querySelectorAll('.star-rating input[type="checkbox"]');

        starInputListener(teacher_star_inputs)
        starInputListener(course_star_inputs)
    }

};


// ===============================================
// Save Button Functionality
// ===============================================

// Check if save button exists
const saveBtn = document.getElementById('saveBtn');
let weekLinks = document.querySelectorAll('a[data-week]');
// Add event listener to save button
if (saveBtn) {
    saveBtn.addEventListener('click', function () {
        // Get the CKEditor instance
        var editor = CKEDITOR.instances.id_description;

        // Get the CKEditor content
        var content = editor.getData();

        // Set the content to a hidden input field
        document.getElementById('id_description').value = content;
    });
}


// ===============================================
// Week Links Handling
// ===============================================

// Define the click event listener function for week links
function weekLinkClickHandler() {
    // Remove active class from all <a> elements
    weekLinks.forEach(function (link) {
        link.classList.remove('active');
    });

    // Add active class to the clicked <a> element
    this.classList.add('active');
}

// Function to attach or detach event listeners for week links
function attachWeekEventListeners(option) {

    // Add or remove click event listener to each <a> element based on the option
    weekLinks.forEach(function (weekLink) {
        if (option === "add") {
            console.log("week works")
            // Add the click event listener
            weekLink.addEventListener('click', weekLinkClickHandler);
        } else if (option === "remove") {
            // Remove the click event listener
            weekLink.removeEventListener('click', weekLinkClickHandler);
        }
    });
}

// Initial attachment of event listeners for week links
attachWeekEventListeners("add");

// ===============================================
// Week Buttons Functionality
// ===============================================

// Add click event listener to week buttons for refreshing event listeners
const weekBtns = document.querySelectorAll('.wkBtn');
if (weekBtns) {
    weekBtns.forEach(function (wkBtn) {
        wkBtn.addEventListener('click', function () {
            // Remove event listeners
            attachWeekEventListeners("remove");

            // Reset active state
            weekLinks.forEach(function (link) {
                link.classList.remove('active');
            });

            // Re-add event listeners after a short delay to allow time for htmx to update the DOM
            setTimeout(function () {
                // Refresh the weekLinks list
                weekLinks = document.querySelectorAll('a[data-week]');

                // Re-add event listeners
                attachWeekEventListeners("add");
            }, 100); // Adjust the delay as needed
        });
    });

}

// ===============================================
// Feedback form stars
// ===============================================


// Add click event listener to each star input
function starInputListener(starInputs) {
    starInputs.forEach(input => {
        input.addEventListener('click', function() {
            // Get the index of the clicked input
            const selectedIndex = Array.from(starInputs).indexOf(input);

            // Loop through all inputs and change their checked state based on the index of the clicked input
            starInputs.forEach((starInput, index) => {
                starInput.checked = index <= selectedIndex; 
            });
        });
    });
}