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


async function loadDashboard() {

    const [
        indexResult,
        historyResult,
        leadTimeResult,
        qualityResult
    ] = await Promise.allSettled([
        fetchData("/index"),
        fetchData("/index/history"),
        fetchData("/lead-times"),
        fetchData("/data-quality")
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

    if (qualityResult.status === "fulfilled") {
        loadQuality(qualityResult.value);
    } else {
        console.error("Data quality failed:", qualityResult.reason);
    }

}


function loadIndex(data) {

    document.getElementById(
        "national-index"
    ).textContent =
        data.national_index.toFixed(2);


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


function loadQuality(data) {

    document.getElementById(
        "source-count"
    ).textContent =
        data.sources;


    document.getElementById(
        "route-count"
    ).textContent =
        data.routes;


    const qualityGrid =
        document.getElementById(
            "quality-grid"
        );


    qualityGrid.innerHTML = `

        <div class="quality-card">

            <div class="info-label">
                RAW RECORDS
            </div>

            <div class="quality-value">
                ${data.raw_records}
            </div>

        </div>


        <div class="quality-card">

            <div class="info-label">
                VALID RECORDS
            </div>

            <div class="quality-value">
                ${data.valid_records}
            </div>

        </div>


        <div class="quality-card">

            <div class="info-label">
                REMOVED RECORDS
            </div>

            <div class="quality-value">
                ${data.removed_records}
            </div>

        </div>


        <div class="quality-card">

            <div class="info-label">
                AIRLINES
            </div>

            <div class="quality-value">
                ${data.airlines}
            </div>

        </div>

    `;

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


document.addEventListener(
    "DOMContentLoaded",
    loadDashboard
);