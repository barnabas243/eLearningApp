const roomName = JSON.parse(document.getElementById('room-name').textContent);
const chatSocket = new WebSocket(
    'wss://'
    + window.location.host
    + '/ws/chat/'
    + roomName
    + '/'
);

// Event handler for when the connection is established
chatSocket.onopen = function (event) {
    console.log('WebSocket connection established.');
    // Send a message to request user data
    chatSocket.send(JSON.stringify({ 'action': "get_user_data" }));
};

// Event handler for receiving messages from the server
chatSocket.onmessage = function (event) {
    // Parse the received data (assuming it's JSON)
    const data = JSON.parse(event.data);
    console.log("data: ", data)
    // Check the type of message received
    if (data.type === 'chat.user_data') {
        if (data.action === "user_connected") {
            // Process the user data
            const users = data.users;
            console.log(users);

            // Your code to remove the 'grey-out' class
            users.forEach((user) => {
                const userBadgeElement = document.getElementById(`${user}_status_badge`);
                const userStatusElement = document.getElementById(`${user}_status_text`);
                if (userBadgeElement && userStatusElement) {
                    userBadgeElement.classList.remove("bg-secondary");
                    userBadgeElement.classList.add("bg-success");
                    userStatusElement.classList.remove("text-secondary");
                    userStatusElement.classList.add("text-success");

                    userStatusElement.textContent = "Online";

                } else {
                    console.error(`Element(s) with ID '${user}' not found.`);
                }
            });
        } else if (data.action === "user_disconnected") {
            // Process the user data
            const user = data.users;
            console.log(user);

            const userBadgeElement = document.getElementById(`${user}_status_badge`);
            const userStatusElement = document.getElementById(`${user}_status_text`);
            if (userBadgeElement && userStatusElement) {
                userBadgeElement.classList.remove("bg-success");
                userBadgeElement.classList.add("bg-secondary");
                userStatusElement.classList.remove("text-success");
                userStatusElement.classList.add("text-secondary");

                userStatusElement.textContent = "Offline";
            }
        }
    } else if (data.type === 'chat.message') {
        if (data.action === "send_message") {
            // Handle other types of messages
            appendMessage(data.message);
        }
    }
};

// Function to append a new message to the chat log
function appendMessage(message) {
    const chatLog = document.querySelector('#messageContainer');
    const messageElement = document.createElement('div');

    // Check if the message is from the current user
    const isCurrentUserMessage = message.username === currentUserName;

    // Add appropriate CSS class based on whether it's the current user's message or not
    const messageClass = isCurrentUserMessage ? 'current-user-message' : 'other-user-message';
    const show_name = isCurrentUserMessage ? '' : message.full_name;

    messageElement.innerHTML = `
                <div class="row">
                    <div class="col">
                        <div class="message text-break ${messageClass}">
                            <div class="message-content">
                                <div class="message-username">${show_name}</div>
                                <div class="message-text">${message.content}</div>
                            </div>
                            <span class="time-left">${message.timestamp}</span>
                        </div>
                    </div>
                </div>
            `;

    chatLog.appendChild(messageElement);
    // Scroll to the bottom of the chat log
    chatLog.scrollTop = chatLog.scrollHeight;
}


// Event handler for errors
chatSocket.onerror = function (error) {
    console.error('WebSocket error:', error);
};

// Event handler for when the connection is closed
chatSocket.onclose = function (event) {
    console.log('WebSocket connection closed.');
    // Send the close event data to the server
    chatSocket.send(JSON.stringify({ 'action': "close_connection", 'close_code': event.code }));
};



const messageInput = document.getElementById('chat-message-input');

/**
 * Replaces URLs in the given text with anchor tags.
 * @param {string} text - The text containing URLs.
 * @returns {string} - The text with URLs replaced by anchor tags.
 */
function replaceURLsWithAnchors(text) {
    const regex = /(https?:\/\/\S+)\s/g;

    return text.replace(regex, function (match) {
        match.trimEnd()
        return `<a href="${match}" target="_blank">${match}</a>`;
    });
}


/**
 * Get the current cursor position 
 * https://phuoc.ng/collection/html-dom/get-or-set-the-cursor-position-in-a-content-editable-element/
 */
function getCurrentCursorPosition() {
    const selection = window.getSelection();
    const range = selection.getRangeAt(0);
    const clonedRange = range.cloneRange();
    clonedRange.selectNodeContents(messageInput);
    clonedRange.setEnd(range.endContainer, range.endOffset);

    const cursorPosition = clonedRange.toString().length;

    return cursorPosition
}
/**
 * Set the cursor position 
 */
function setCursorPosition(targetPosition) {
    let currentNode = messageInput.firstChild;
    let charCount = 0;

    // Traverse the DOM nodes to find the correct position
    while (currentNode && charCount < targetPosition) {
        if (currentNode.nodeType === Node.TEXT_NODE) {
            const textLength = currentNode.textContent.length;
            if (charCount + textLength >= targetPosition) {
                const range = document.createRange();
                range.setStart(currentNode, targetPosition - charCount);
                range.collapse(true);

                const selection = window.getSelection();
                selection.removeAllRanges();
                selection.addRange(range);
                return;
            }
            charCount += textLength;
        }

        // Move to the next node
        const nextNode = currentNode.nextSibling;
        if (nextNode) {
            currentNode = nextNode;
        } else {
            currentNode = currentNode.parentNode.nextSibling;
        }
    }
}
function getLastPos() {
    // Get the text content of the div
    const textContent = messageInput.textContent;

    // Return the length of the text content
    return textContent.length;
}
messageInput.addEventListener('input', function () {
    const text = this.textContent;
    const originalCursorPos = getCurrentCursorPosition();
    console.log("Original Cursor Position: ", originalCursorPos);

    // Replace URLs with anchor tags
    const replacedText = replaceURLsWithAnchors(text);
    this.innerHTML = replacedText;

    // Calculate adjusted cursor position after replacing URLs
    const adjustedCursorPos = originalCursorPos + replacedText.length - text.length;
    console.log("Adjusted Cursor Position: ", adjustedCursorPos);
    console.log("Original Cursor Position: ", originalCursorPos);
    console.log("get last position: ",getLastPos())
    // // Set the cursor position
    // setCursorPosition(adjustedCursorPos);
    setCursorPosition(originalCursorPos);
    this.focus();

});
messageInput.addEventListener('click', function(){
    console.log("current pos: ",getCurrentCursorPosition() )
})
messageInput.addEventListener('keydown', function (event) {
    // Check if the Enter key is pressed
    if (event.key === 'Enter') {
        // Prevent the default behavior of the Enter key
        event.preventDefault();
        // Insert a line break at the current cursor position
        const selection = window.getSelection();
        const range = selection.getRangeAt(0);
        const br = document.createElement('br');
        range.insertNode(br);
        range.setStartAfter(br);
        range.collapse(true);
        selection.removeAllRanges();
        selection.addRange(range);

        messageInput.scrollTop = messageInput.scrollHeight;
    }
});

messageInput.focus();
document.querySelector('#chat-message-form').onsubmit = function (e) {
    e.preventDefault();
    const messageInputDom = document.querySelector('#chat-message-input');
    const content = messageInputDom.innerHTML;
    const chatRoomId = document.querySelector('#chat-room-id').value;

    // Ensure all required fields are provided
    if (content && chatRoomId) {
        const message = {
            'chat_room': chatRoomId,
            'content': content
        };

        chatSocket.send(JSON.stringify({
            'message': message
        }));
        messageInputDom.innerHTML = '';
        messageInputDom.rows = 1;
    } else {
        console.error("Missing required fields for message creation.");
    }
}


const imageModal = document.querySelector('#imageModal')
const enlargedImage = document.querySelector("#enlargedImage");

imageModal.addEventListener('show.bs.modal', function (e) {
    const link = e.relatedTarget;
    const imgSrc = link.getAttribute("data-image-src");

    enlargedImage.src = imgSrc;
})
