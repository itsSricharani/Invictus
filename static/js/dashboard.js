async function fetchData(endpoint) {

    const response = await fetch(endpoint);

    if (!response.ok) {
        throw new Error(
            `Failed to load ${endpoint}`
        );
    }

    return await response.json();
}


function formatDate(dateString) {

    const date = new Date(
        dateString + "T00:00:00"
    );

    return date.toLocaleDateString(
        "en-IN",
        {
            day: "2-digit",
            month: "short",
            year: "numeric"
        }
    );
}

function initScrollReveal() {
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


function animateCountUp(element, targetValue, duration = 900) {
    const startValue = 0;
    const startTime = performance.now();

    function step(now) {
        const progress = Math.min(
            (now - startTime) / duration,
            1
        );

        // ease-out cubic
        const eased = 1 - Math.pow(1 - progress, 3);

        const current =
            startValue + (targetValue - startValue) * eased;

        element.textContent = current.toFixed(2);

        if (progress < 1) {
            requestAnimationFrame(step);
        } else {
            element.textContent = targetValue.toFixed(2);
        }
    }

    requestAnimationFrame(step);
}


async function loadDashboard() {

    const [
        indexResult,
        historyResult,
        leadTimeResult,
        qualityResult
    ] = await Promise.allSettled([
        fetchData("/index"),
        fetchData("/index/history"),
        fetchData("/lead-times")
    ]);

    if (indexResult.status === "fulfilled") {
        loadIndex(indexResult.value);
        loadRoutes(indexResult.value);
    } else {
        console.error("Index failed:", indexResult.reason);
        document.getElementById("national-index").textContent = "Error";
        document.getElementById("index-change").textContent =
            "Unable to load index data";
    }

    if (historyResult.status === "fulfilled") {
        loadHistoryChart(historyResult.value);
    } else {
        console.error("History failed:", historyResult.reason);
    }

    if (leadTimeResult.status === "fulfilled") {
        loadLeadTimes(leadTimeResult.value);
    } else {
        console.error("Lead times failed:", leadTimeResult.reason);
    }

}


function loadIndex(data) {

    const demoBanner = document.getElementById("demo-banner");
    const statusElem = document.querySelector(".nav-status");

    if (data.data_mode === "demo") {
        if (demoBanner) demoBanner.style.display = "block";
        if (statusElem) {
            statusElem.style.background = "#e65100";
            statusElem.innerHTML = '<span class="status-dot" style="background:#ffcc80"></span> DEMO MODE (FALLBACK DATA)';
        }
    } else {
        if (demoBanner) demoBanner.style.display = "none";
        if (statusElem) {
            statusElem.style.background = "";
            statusElem.innerHTML = '<span class="status-dot"></span> LIVE DATA';
        }
    }

     animateCountUp(
        document.getElementById("national-index"),
        data.national_index
    );



    document.getElementById(
        "base-date"
    ).textContent =
        formatDate(data.base_date);


    document.getElementById(
        "current-period"
    ).textContent =
        formatDate(data.current_date);


    document.getElementById(
        "current-date"
    ).textContent =
        formatDate(data.current_date);


    const change =
        data.national_index - 100;


    const sign =
        change >= 0 ? "+" : "";


    document.getElementById(
        "index-change"
    ).textContent =
        `${sign}${change.toFixed(2)} points from base period`;

}


function loadRoutes(data) {

    const routeGrid =
        document.getElementById(
            "route-grid"
        );


    routeGrid.innerHTML = "";


    Object.entries(
        data.route_indices
    ).forEach(
        ([route, value]) => {

            const change =
                value - 100;

            const sign =
                change >= 0 ? "+" : "";


            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "route-card";


            card.innerHTML = `

                <div class="route-name">
                    ${route}
                </div>

                <div class="route-value">
                    ${value.toFixed(2)}
                </div>

                <div class="route-status">
                    ${sign}${change.toFixed(2)}
                    points from base
                </div>

            `;


            routeGrid.appendChild(
                card
            );

        }
    );

}


function loadLeadTimes(data) {

    const container =
        document.getElementById(
            "lead-time-grid"
        );


    container.innerHTML = "";


    Object.entries(
        data.lead_time_indices
    ).forEach(
        ([leadTime, value]) => {

            const card =
                document.createElement(
                    "div"
                );


            card.className =
                "lead-card";


            card.innerHTML = `

                <div class="lead-label">
                    ${leadTime} Booking Window
                </div>

                <div class="lead-value">
                    ${value.toFixed(2)}
                </div>

            `;


            container.appendChild(
                card
            );

        }
    );

}


function loadHistoryChart(data) {

    const labels =
        data.history.map(
            item => formatDate(item.date)
        );


    const values =
        data.history.map(
            item => item.index
        );


    const ctx =
        document.getElementById(
            "history-chart"
        );


    new Chart(
        ctx,
        {
            type: "line",

            data: {
                labels: labels,

                datasets: [
                    {
                        label:
                            "National APIx",

                        data: values,

                        borderWidth: 3,

                        tension: 0.35,

                        pointRadius: 4
                    }
                ]
            },

            options: {

                responsive: true,

                maintainAspectRatio: false,

                plugins: {

                    legend: {
                        display: false
                    }

                },

                scales: {

                    y: {
                        beginAtZero: false
                    }

                }

            }
        }
    );

}


document.addEventListener("DOMContentLoaded", () => {
    initScrollReveal();
    loadDashboard();
});