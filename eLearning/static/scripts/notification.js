function custom_notification_callback(data) {
    const notificationList = document.getElementById('notification-list');
    const messageBadge = document.querySelector('.badge')

    if (messageBadge) editBadgeCount(data.unread_list.length)
    // Clear existing notifications
    notificationList.innerHTML = '';


    if (data.unread_list.length === 0) {
        const p = document.createElement('p');
        p.classList.add('p-3')
        p.textContent = "You have no notifications at the moment."
        notificationList.append(p)

        return
    }

    // Loop through the notifications data and create list items for each notification
    data.unread_list.map(function (notification) {
        const li = document.createElement('li');

        // show time passed since notification sent
        const timestamp = dayjs(notification.timestamp).tz(dayjs.tz.guess()).fromNow();

        // Create notification content
        const div = document.createElement('div');
        div.className = 'd-flex justify-content-between align-items-center gap-4 mb-3';
        div.innerHTML = `
        <div>
            <strong>${notification.actor}</strong>
        </div>
        <div>
            <time class="fst-italic" datetime="${notification.timestamp}">${timestamp}</time>
        </div>
        <a href="#" data-notification-id="${notification.id}" class="text-danger fs-5"><i class="fas fa-times"></i></a>
        `;
        li.appendChild(div);

        // Create verb paragraph
        const p = document.createElement('p');
        p.innerHTML = notification.verb;
        li.appendChild(p);

        li.classList.add('live-notification-li', 'mx-4', 'my-3', 'border-1', 'border-danger', 'bg-light');
       
        // Apply cursor pointer style
        li.classList.add('clickable');

        // get link from p tag. hacky method but didnt see another way
        li.dataset.link = p.querySelector('a').href;

        // Append list item to notification list
        notificationList.appendChild(li);

        // add eventListener to remove the read notification
        li.addEventListener('click', function (event) {
            // Check if the event target is not an anchor element
            if (event.target.tagName !== 'A') {
                markAsRead(dismissBtn);
                window.location.href = li.dataset.link;
            }
        });


        const dismissBtn = li.querySelector('a');
        dismissBtn.addEventListener('click', function (event) {
            event.stopPropagation(); // Prevent the click event from propagating to the <li> element
            markAsRead(this);
        });

    });
}

function dismissNotification(notificationItem) {
    // Add class for animation
    notificationItem.classList.add('removing');

    // Remove the notification item from the DOM after a delay
    setTimeout(function () {
        notificationItem.remove();
        const notifCount = document.querySelectorAll('.live-notification-li').length;
        editBadgeCount(notifCount)
    }, 300); // Adjust the delay to match the transition duration
}

function markAsRead(dismissBtn) {
    const id = dismissBtn.dataset.notificationId;

    const host = window.location.host // Assuming your base URL has 3 segments

    const url = `https://${host}/inbox/notifications/mark-as-read/${id}/`;
    const csrftoken = getCookie('csrftoken');
    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken,
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to mark notification as read');
            }
            // Handle success
            console.log('Notification marked as read successfully');
            // Optionally, you can also remove the notification from the UI after marking it as read
            dismissNotification(dismissBtn.closest('.live-notification-li'));
        })
        .catch(error => {
            // Handle error
            console.error('Error marking notification as read:', error);
        });
}

// Function to retrieve the CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Check if this cookie name is the one we are looking for
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function editBadgeCount(notifCount) {
    const messageBadge = document.querySelector('.badge')

    if (notifCount > 0) {
        messageBadge.textContent = notifCount
        messageBadge.classList.remove('visually-hidden')
    } else {
        messageBadge.classList.add('visually-hidden')
    }
}