const modal = document.getElementById("gameModal");
const modalTitle = document.getElementById("modalGameTitle");
const modalInfo = document.getElementById("modalGameInfo");


document.querySelectorAll(".details-btn").forEach(btn => {
btn.addEventListener("click", () => {
    modalTitle.textContent = btn.dataset.title;
    modalInfo.textContent = btn.dataset.info;
    modal.style.display = "flex";
});
});

function closeModal() {
modal.style.display = "none";
}

window.addEventListener("click", e => {
if (e.target === modal) closeModal();
});