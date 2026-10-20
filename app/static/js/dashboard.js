// Supervisor Operations Dashboard Chart.js Initialization

document.addEventListener('DOMContentLoaded', function() {
    const riskCtx = document.getElementById('riskDistributionChart');
    if (riskCtx) {
        const low = parseInt(riskCtx.getAttribute('data-low') || '0');
        const mod = parseInt(riskCtx.getAttribute('data-moderate') || '0');
        const high = parseInt(riskCtx.getAttribute('data-high') || '0');
        const crit = parseInt(riskCtx.getAttribute('data-critical') || '0');

        new Chart(riskCtx, {
            type: 'bar',
            data: {
                labels: ['LOW', 'MODERATE', 'HIGH', 'CRITICAL'],
                datasets: [{
                    label: 'Officer Workload Risk Distribution',
                    data: [low, mod, high, crit],
                    backgroundColor: [
                        '#4F7D5A', // LOW
                        '#B18435', // MODERATE
                        '#B7653C', // HIGH
                        '#9B3F3F'  // CRITICAL
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    title: { display: true, text: 'Active Officers Workload Risk Breakdown' }
                },
                scales: {
                    y: { beginAtZero: true, ticks: { stepSize: 1 } }
                }
            }
        });
    }
});
