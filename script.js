// Selecting DOM elements
const selectImage = document.querySelector('.select-image');
const inputFile = document.querySelector('#file');
const imgArea = document.querySelector('.img-area');

let imageSelected = false; // Flag to track if an image is already selected

// Event listener for clicking on the "Select Image" button
selectImage.addEventListener('click', function () {
    // Check if an image is already selected
    if (!imageSelected) {
        inputFile.click(); // Trigger the file input click event to select an image
    } else {
        alert("You have already selected an image. Please proceed with the current selection.");
    }
})

// Event listener for file input change (when an image is selected)
inputFile.addEventListener('change', function () {
    const image = this.files[0]; // Get the selected image file
    if (!imageSelected && image.size < 2000000) { // Check if an image is not already selected and if the image size is within limit
        const reader = new FileReader();
        reader.onload = () => {
            const allImg = imgArea.querySelectorAll('img');
            allImg.forEach(item => item.remove()); // Remove any existing images in the image area
            const imgUrl = reader.result; // Get the image URL
            const img = document.createElement('img'); // Create a new image element
            img.src = imgUrl; // Set the image source
            imgArea.appendChild(img); // Append the image to the image area
            imgArea.classList.add('active'); // Add the 'active' class to show the image area
            imgArea.dataset.img = image.name; // Set the dataset attribute with the image name
            imageSelected = true; // Set the flag to true once an image is selected
        }
        reader.readAsDataURL(image); // Read the image data as a URL
    } else if (imageSelected) {
        alert("You have already selected an image. Please proceed with the current selection.");
    } else {
        alert("Image size more than 2MB");
    }
})