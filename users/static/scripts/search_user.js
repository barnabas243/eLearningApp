// ===============================================
// Search Functionality
// ===============================================

// Function to handle search input
function handleSearchInput(event) {
    if (event.key === 'Enter') {
        const searchValue = searchInput.value.trim();
        if (searchValue !== '') {
            navigateToSearchURL(searchValue);
        }
    }
}

// Function to navigate to the search URL
function navigateToSearchURL(searchValue) {
    window.location.href = `/home/search?q=${encodeURIComponent(searchValue)}`;
}

// Function to handle user input
function handleUserInput() {
    var val = searchInput.value;
    var opts = document.getElementById('searchOptions').children;
    for (var i = 0; i < opts.length; i++) {
        if (opts[i].value === val) {
            navigateToUserHomePage(opts[i].value);
            break;
        }
    }
}

// Function to navigate to the user's home page
function navigateToUserHomePage(selectedUser) {
    window.location.href = `/home/search/${encodeURIComponent(selectedUser)}`;
}

// Get the search input element
const searchInput = document.getElementById('searchInput');

// Check if search input exists
if (searchInput) {
    // Add event listener for keydown on search input
    searchInput.addEventListener('keydown', handleSearchInput);
    searchInput.addEventListener('input', handleUserInput);
}
