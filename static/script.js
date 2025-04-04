document.getElementById("videoForm").addEventListener("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission

    let form = new FormData(this);

    fetch("/video", {
        method: "POST",
        body: form,
    })
    .then(response => {
        if (!response.ok) throw new Error("Download failed");

        return response.blob(); // Convert response to file blob
    })
    .then(blob => {
        // Create a download link and trigger it
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "video.mp4"; // Set the filename
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showPopup("Download Complete!", true);

        // Reload after 2 seconds to fix UI issues
        setTimeout(() => window.location.reload(), 2000);
    })
    .catch(() => {
        showPopup("Download Failed. Please try again.", false);
    });
});
document.getElementById("instagramform").addEventListener("submit", function (e) {
    e.preventDefault(); // Prevent the default form submission

    let form = new FormData(this);

    fetch("/instagram", {
        method: "POST",
        body: form,
    })
    .then(response => {
        if (!response.ok) throw new Error("Download failed");

        return response.blob(); // Convert response to file blob
    })
    .then(blob => {
        // Create a download link and trigger it
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "image.jpeg"; // Set the filename
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        showPopup("Download Complete!", true);

        // Reload after 2 seconds to fix UI issues
        setTimeout(() => window.location.reload(), 2000);
    })
    .catch(() => {
        showPopup("Download Failed. Please try again.", false);
    });
});
// Function to show popup messages
function showPopup(message, isSuccess = true) {
    const popup = document.createElement("div");
    popup.classList.add("popup");
    popup.textContent = message;

    if (!isSuccess) {
        popup.classList.add("failed");
    }

    document.body.appendChild(popup);
    popup.style.display = "block";

    setTimeout(() => {
        popup.style.display = "none";
        popup.remove();
    }, 3000);
}

document.querySelector("videoForm").addEventListener("submit", function(e) {
    e.preventDefault(); // Prevent default form submission

    const formData = new FormData(this);

    fetch("/instagram", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPopup("Download Complete!", true);
        } else {
            showPopup("Download Failed. Please try again.", false);
        }
    })
    .catch(() => {
        showPopup("An error occurred. Please try again.", false);
    });
});
// Function to show popup message
function showPopup(message, isSuccess) {
    const popup = document.createElement("div");
    popup.classList.add("popup");
    popup.textContent = message;
    
    if (!isSuccess) {
        popup.classList.add("failed");
    }

    document.body.appendChild(popup);
    popup.style.display = "block";

    setTimeout(() => {
        popup.style.display = "none";
        popup.remove();
    }, 3000);
}