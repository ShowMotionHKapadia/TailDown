//Load Js in DOM
$(document).ready(function() {
    // Iterate through each message data element for Toastify notifications
    $("#django-messages .message-data").each(function() {
        const msgText = $(this).data("text");
        const msgTag = $(this).data("tag");

        // Use your common function!
        showNotification(msgText, msgTag);
    });

});

// Common function to show notifications using Toastify
function showNotification(msg, type) {
    // Define colors based on tags
    var bgColor = " #00D062"; 
    if (type === "error" || type === "danger") {
        bgColor = "#fd1515e9"; 
    } else if (type === "warning") {
        bgColor = "#f9d338"; // Yellow
    } else if (type === "info") {
        bgColor = "#29d0f9"; // Blue
    }

    Toastify({
        text: msg,
        duration: 4000,
        close: true,    
        gravity: "top",
        position: "right",
        stopOnFocus: true,
        offset: {
            x: 20, // horizontal axis: distance from right
            y: 70  // vertical axis: distance from top (push it below your header)
        },
        style: {
            background: bgColor,
            width: "auto",            // Set to auto so it expands with text
            minWidth: "250px",        // Ensures it's not too small
            maxWidth: "350px",        // Ensures it doesn't get too big
            minHeight: "50px",
            display: "flex",          // Enables Flexbox
            justifyContent: "flex-start", // Centers text horizontally
            arguments: "center",       // Centers text vertically
            fontSize: "15px",
            fontWeight: "500",
        }
    }).showToast();
}

