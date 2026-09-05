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

document.addEventListener("DOMContentLoaded", () => {
    openIntroPanel();
    initLandingReveal();
});