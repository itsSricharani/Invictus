function openIntroPanel() {
    const panel = document.getElementById("introPanel");

    setTimeout(() => {
        panel.classList.add("opened");
    }, 500);
}

function initLandingReveal() {
    const targets = document.querySelectorAll(".reveal");

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15 }
    );

    targets.forEach((target) => observer.observe(target));
}

async function loadLandingIndex() {
    const el = document.getElementById("landingIndexValue");

    try {
        const response = await fetch("/index");
        const data = await response.json();
        el.textContent = data.national_index.toFixed(2);
    } catch (error) {
        el.textContent = "—";
        console.error("Landing index fetch failed:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    openIntroPanel();
    initLandingReveal();
    loadLandingIndex();
});