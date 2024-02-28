// ===============================================
// WebSocket Connection 
// ===============================================
const roomName = JSON.parse(document.getElementById('room-name').textContent).toLowerCase().replace(/ /g, '-');

const chatSocket = new WebSocket(
    'wss://'
    + window.location.host
    + '/ws/chat/'
    + roomName
    + '/'
);

const chatRoomId = document.querySelector('#chat-room-id').value;

const messageContainer = document.querySelector('#messageContainer');

let last_viewed_message;

const scrollConfig = {
    behavior: 'instant', // smoothscrolling is too slow
}
// Event handler for when the connection is established
chatSocket.onopen = function (event) {
    console.log('WebSocket connection established.');
    // Send a message to request user data
    chatSocket.send(JSON.stringify({ 'action': "get_user_data", 'chat_room_id': chatRoomId }));
};

// Event handler for receiving messages from the server
chatSocket.onmessage = function (event) {
    // Parse the received data (assuming it's JSON)
    const data = JSON.parse(event.data);
    console.log("data: ", data);

    // Process the received message based on its type
    switch (data.type) {
        case 'chat.user_data':
            handleUserDataMessage(data);
            break;
        case 'chat.message':
            handleMessage(data);
            break;
        default:
            console.error('Unknown message type:', data.type);
    }
};

function scrollToLastViewedMessage(message_id) {
    // Find the message element with the matching data-message-id attribute
    if (!message_id) {
        console.error("last_viewed message doesnt exist")
        return
    }
    const messageDiv = document.querySelector(`div[data-message-id="${message_id}"]`);

    if (messageDiv) {
        // Scroll to the top position of the message element
        messageDiv.scrollIntoView(scrollConfig);
        messageDiv.parentNode.classList.add('flash');

        setTimeout(() => {
            messageDiv.parentNode.classList.remove('flash');
        }, 800);
        

        last_viewed_message = message_id
    } else {
        console.error(`Message with ID ${message_id} not found.`);
    }
}

// Function to handle user data messages
function handleUserDataMessage(data) {
    // Determine the action in the user data message
    switch (data.action) {
        case 'user_last_viewed_message':
            scrollToLastViewedMessage(data.last_viewed_message)
            break;
        case 'user_connected':
            processConnectedUsers(data.users);
            break;
        case 'user_disconnected':
            processDisconnectedUser(data.users);
            break;
        default:
            console.error('Unknown action in user data message:', data.action);
    }
}
// Function to process connected users
function processConnectedUsers(users) {
    console.log('Connected users:', users);
    // Update UI to show users as online
    users.forEach((user) => {
        updateUserStatus(user, true);
    });
}

// Function to process disconnected user
function processDisconnectedUser(user) {
    // Update UI to show user as offline
    updateUserStatus(user, false);
}

// Function to update user status in the UI
function updateUserStatus(user, isOnline) {
    const userBadgeElement = document.getElementById(`${user}_status_badge`);
    const userStatusElement = document.getElementById(`${user}_status_text`);
    if (userBadgeElement && userStatusElement) {
        if (isOnline) {
            userBadgeElement.classList.remove("bg-secondary");
            userBadgeElement.classList.add("bg-success");
            userStatusElement.classList.remove("text-secondary");
            userStatusElement.classList.add("text-success");
            userStatusElement.textContent = "Online";
        } else {
            userBadgeElement.classList.remove("bg-success");
            userBadgeElement.classList.add("bg-secondary");
            userStatusElement.classList.remove("text-success");
            userStatusElement.classList.add("text-secondary");
            userStatusElement.textContent = "Offline";
        }

        updateLastOnlineStatus()
    } else {
        console.error(`Element(s) with ID '${user}' not found.`);
    }
}

// Function to handle message data messages
function handleMessage(data) {
    // Handle other types of messages
    if (data.action === "send_message") {
        appendMessage(data.message);
        console.log("data.message.id: ", data.message.id)
        last_viewed_message = data.message.id
    } else {
        console.error('Unknown action in message data:', data.action);
    }
}

/**
 * Append a new message to the chat log.
 * @param {Object} message - The message object containing details of the message.
 * @param {number} message.id - The unique identifier of the message.
 * @param {string} message.content - The content of the message.
 * @param {string} message.username - The username of the sender.
 * @param {string} message.full_name - The full name of the sender.
 * @param {string} message.timestamp - The timestamp of the message.
 */
function appendMessage(message) {
    // Check if the chat log container exists
    if (!messageContainer) {
        console.error("Chat log container not found.");
        return;
    }


    // Convert the message timestamp to local time
    const localTime = formatISOtoLocalTime(message.timestamp);

    // Find the last message element with a data-timestamp attribute
    const lastMessage = messageContainer.querySelector('div[data-timestamp]:last-child');

    // Check if the chat log is empty or if the new message has a different date from the last message
    if (!lastMessage || new Date(formatISOtoLocalTime(lastMessage.dataset.timestamp)).toDateString() !== new Date(localTime).toDateString()) {
        // Create a date header
        const dateHeader = document.createElement('div');
        dateHeader.classList.add('d-flex', 'justify-content-center', 'align-items-center', 'my-3');
        dateHeader.innerHTML = `
            <hr style="border-top: 1px solid #ccc; flex-grow: 1; margin: 0;">
            <div class="message-date-header">
                <span class="badge bg-light text-secondary">${localTime.toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
            </div>
            <hr style="border-top: 1px solid #ccc; flex-grow: 1; margin: 0;">
        `;
        // Append the date header to the chat log
        messageContainer.appendChild(dateHeader);
    }

    // Replace URLs in the message content with anchor tags
    const urlized_content = replaceURLsWithAnchors(message.content);
    // Determine if the message is from the current user
    const isCurrentUserMessage = message.username === currentUserName;
    // Define CSS class based on message sender
    const messageClass = isCurrentUserMessage ? 'current-user-message' : 'other-user-message';
    // Determine the display name of the message sender
    const show_name = isCurrentUserMessage ? '' : message.full_name;

    // Construct the HTML structure for the message element
    
    // Create a new message element
    const messageElement = document.createElement('div');
    messageElement.classList.add('row');
    messageElement.innerHTML = `
        <div class="col">
            <div class="message text-break ${messageClass}" data-message-id="${message.id}" data-timestamp="${message.timestamp}">
                <div class="message-content">
                    <div class="message-username">${show_name}</div>
                    <div class="message-text">${urlized_content}</div>
                </div>
                <span class="time-right text-primary">${localTime.toLocaleString()}</span>
            </div>
        </div>
    `;

    // Append the message element to the chat log
    messageContainer.appendChild(messageElement);

    // Scroll to the newly appended message
    messageElement.scrollIntoView(scrollConfig);
}


// Event handler for errors
chatSocket.onerror = function (error) {
    console.error('WebSocket error:', error);
};

// Event handler for when the connection is closed
chatSocket.onclose = function (event) {
    console.log('WebSocket connection closed.');
    // Send the close event data to the server
    // chatSocket.send(JSON.stringify(
    //     {
    //         'action': "close_user_connection",
    //         'close_code': event.code,
    //         'chat_room_id': chatRoomId,
    //         'last_viewed_message': last_viewed_message
    //         // get last read message id from the dom
    //     }));
};

window.addEventListener('beforeunload', function (event) {
    // Code to execute before the page is unloaded
    // Example: Send data via WebSocket
    chatSocket.send(JSON.stringify({
        'action': "close_user_connection",
        'chat_room_id': chatRoomId,
        'last_viewed_message': last_viewed_message
    }));

    // Customize the confirmation message if needed
    //event.returnValue = 'Are you sure you want to leave?';
});


// Function to update last online status
function updateLastOnlineStatus() {
    const users_last_online = document.querySelectorAll('div[data-last-online]');

    if (users_last_online) {
        users_last_online.forEach((user) => {
            const last_online_span = user.querySelectorAll('span')[1];

            if (last_online_span && last_online_span.classList.contains('text-secondary')) {
                const timestamp = user.dataset.lastOnline;
                // console.log(timestamp)
                if (timestamp) {
                    const time_since_timestamp = dayjs.utc(timestamp).from(dayjs())
                    // online a month ago
                    last_online_span.textContent = `online ${time_since_timestamp}`;
                }
            }
        });
    }
}

// Initial call to update last online status
updateLastOnlineStatus();

// Polling function to update last online status every 1 minute
setInterval(updateLastOnlineStatus, 60000); // 60000 milliseconds = 1 minute

const chatUserSearchInput = document.getElementById('chatUserSearchInput');
const usersList = document.getElementById('usersList');

chatUserSearchInput.addEventListener('input', function () {
    const searchTerm = this.value.toLowerCase();
    const users = usersList.querySelectorAll('div[data-username]');

    users.forEach(function (user) {
        user.querySelector('a')
        const full_name = user.querySelector('a').textContent.toLowerCase();
        if (full_name.includes(searchTerm)) {
            user.classList.remove('visually-hidden');
        } else {
            user.classList.add('visually-hidden');
        }
    });
});
// ===============================================
// Messages
// ===============================================
const messageInput = document.getElementById('chat-message-input');
autosize(messageInput); // initialize autosize for textarea
messageInput.dispatchEvent(new Event('input', { bubbles: true }));
messageInput.focus();

// format dates with dayjs
document.querySelectorAll('div[data-timestamp]').forEach((timestamp) => {
    const ISOtimestamp = timestamp.dataset.timestamp;
    const localTime = formatISOtoLocalTime(ISOtimestamp)

    timestamp.querySelector('span').textContent = localTime;
});

function formatISOtoLocalTime(timestamp) {
    const localTime = dayjs(timestamp).tz(dayjs.tz.guess()).format('h:mm a');
    
    return localTime;
}

/**
 * Replaces URLs in the given text with anchor tags.
 * @param {string} text - The text containing URLs.
 * @returns {string} - The text with URLs replaced by anchor tags.
 */
function replaceURLsWithAnchors(text) {
    const regex = /(https?:\/\/\S+)(?:\s|$)/g

    return text.replace(regex, function (match) {
        const trimmed = match.trimEnd()
        return `<a href="${trimmed}" target="_blank">${trimmed}</a>`;
    });
}



document.querySelector('#chat-message-form').onsubmit = function (e) {
    e.preventDefault();
    const messageInputDom = document.querySelector('#chat-message-input');
    const content = messageInputDom.value;

    // Ensure all required fields are provided
    if (content && chatRoomId) {
        const message = {
            'chat_room': chatRoomId,
            'content': content
        };

        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.value = '';
        messageInputDom.rows = 1;

    } else {
        console.error("Missing required fields for message creation.");
    }
}


// Attach a scroll event listener to the messageContainer
messageContainer.parentNode.addEventListener('scroll', function() {
    console.log("scrolling")
    // Get all message blocks inside the messageContainer
    const messageBlocks = messageContainer.querySelectorAll('div[data-message-id]');

    // Calculate the distance between each message block and the bottom of the container
    // Get the scrolling parent node of messageContainer
    const scrollingParent = messageContainer.parentNode;

    // Calculate the height of the scrolling parent node from the top of the body
    const containerHeight = scrollingParent.offsetHeight + scrollingParent.offsetTop;

    // Get the scroll position of the scrolling parent
    const scrollPosition = scrollingParent.scrollTop;
    
    const closestBlock = Array.from(messageBlocks).reduce((closest, block) => {
        const blockTop = block.offsetTop - scrollPosition;
        const blockBottom = blockTop + block.offsetHeight; // Calculate the bottom of the block
        const distanceToBottom = containerHeight - blockBottom;
        if (distanceToBottom > 0 && distanceToBottom < closest.distance) {
            return { block, distance: distanceToBottom };
        } else {
            return closest;
        }
    }, { block: null, distance: Infinity }).block;
    
    

    // Perform the desired action with the closest message block
    if (closestBlock) {
        // console.log("closestBlock: ",closestBlock)
        // console.log("closestBlock.dataset.messageId: ",closestBlock.dataset.messageId)
        last_viewed_message = closestBlock.dataset.messageId
        // Example: Add a class to highlight the closest block
        // closestBlock.classList.add('highlight');
    }
});

// ===============================================
// Image Modal Logic
// ===============================================

// Get the image modal and enlarged image elements
const imageModal = document.querySelector('#imageModal');
const enlargedImage = document.querySelector("#enlargedImage");

// Event listener for when the image modal is shown
imageModal.addEventListener('show.bs.modal', function (e) {
    // Get the link that triggered the modal
    const link = e.relatedTarget;
    // Get the image source from the data attribute of the link
    const imgSrc = link.dataset.imageSrc;
    // Set the source of the enlarged image in the modal
    enlargedImage.src = imgSrc;
});

// ===============================================
// File Input and File Preview Modal Logic
// ===============================================

// Get the file input, file preview modal, file modal trigger,
// file preview image, and caption input elements
const fileInput = document.querySelector('#file-input');
const filePreviewModal = document.getElementById('filePreviewModal');
const fileModalTrigger = document.querySelector('#fileModalTrigger');
const filePreviewImage = document.getElementById('file-preview');
const captionInput = document.getElementById('caption');

// Event listener for file input change
fileInput.addEventListener('change', function () {
    // Get the selected file
    const file = this.files[0];
    if (file) {
        // Read the file and set the file preview image source
        const reader = new FileReader();
        reader.onload = function (event) {
            filePreviewImage.src = event.target.result;
            // Trigger the file preview modal to show
            fileModalTrigger.click();
        };
        reader.readAsDataURL(file);
    }
});

// Event listener for when the file preview modal is hidden
filePreviewModal.addEventListener('hide.bs.modal', function () {
    // Reset file input value
    fileInput.value = '';
    // Reset caption input
    captionInput.value = '';
    // Reset file preview image source
    filePreviewImage.src = '#';
});
