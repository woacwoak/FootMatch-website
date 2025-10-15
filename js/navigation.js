// ================= MOBILE NAVIGATION TOGGLE =================
const hamburger = document.querySelector(".hamburger");
const navLinks = document.querySelector("#hamburger-header-nav");
const navLinkItems = document.querySelectorAll("#hamburger-header-nav a");

// Toggle mobile nav when hamburger is clicked
hamburger.addEventListener("click", () => {
    navLinks.classList.toggle("nav-open");
    // Animate hamburger bars (optional)
    hamburger.classList.toggle("open");
});

// Optional: Close mobile nav when a link is clicked
navLinkItems.forEach(link => {
    link.addEventListener("click", () => {
        navLinks.classList.remove("nav-open");
        hamburger.classList.remove("open");
    }); 
});