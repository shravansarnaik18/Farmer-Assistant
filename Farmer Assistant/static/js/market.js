// Market Price Auto-Update System

document.addEventListener("DOMContentLoaded", function() {
    
    // Initialize chart if price data exists
    if (typeof priceData !== "undefined" && priceData.length > 0) {
        createPriceChart();
    }
    
    // Auto-refresh prices every 5 minutes (300000 ms)
    setInterval(updateMarketPrices, 300000);
    
    // Add event listener for crop selection
    const cropSelect = document.getElementById('cropSelect');
    if (cropSelect) {
        cropSelect.addEventListener('change', function() {
            if (this.value) {
                submitMarketForm();
            }
        });
    }
});

function createPriceChart() {
    const labels = priceData.map(row => row.date);
    const prices = priceData.map(row => row.price);

    const ctx = document.getElementById('priceChart');
    if (ctx) {
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Price Trend (₹/Quintal)',
                    data: prices,
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 5,
                    pointBackgroundColor: '#667eea',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointHoverRadius: 7
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            font: { size: 14, weight: 'bold' },
                            color: '#333'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0,0,0,0.8)',
                        padding: 15,
                        titleFont: { size: 14 },
                        bodyFont: { size: 13 },
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return '₹' + context.parsed.y.toFixed(2) + '/Quintal';
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        ticks: {
                            callback: function(value) {
                                return '₹' + value;
                            }
                        },
                        grid: {
                            color: 'rgba(0,0,0,0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

function updateMarketPrices() {
    const cropSelect = document.getElementById('cropSelect');
    if (!cropSelect || !cropSelect.value) {
        console.log('No crop selected for auto-update');
        return;
    }
    
    const selectedCrop = cropSelect.value;
    
    fetch(`/api/market/prices/${encodeURIComponent(selectedCrop)}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch prices');
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.prices.length > 0) {
                // Update global priceData for chart
                window.priceData = data.prices;
                
                // Recreate chart with updated data
                const existingCanvas = document.getElementById('priceChart');
                if (existingCanvas) {
                    // Destroy existing chart instance
                    const canvasParent = existingCanvas.parentElement;
                    existingCanvas.remove();
                    
                    // Create new canvas
                    const newCanvas = document.createElement('canvas');
                    newCanvas.id = 'priceChart';
                    canvasParent.appendChild(newCanvas);
                    
                    createPriceChart();
                }
                
                // Update table if exists
                updatePriceTable(data.prices);
                
                // Show update notification
                showUpdateNotification('Market prices updated');
                
                console.log(`Updated prices for ${selectedCrop}`);
            }
        })
        .catch(error => {
            console.error('Error updating prices:', error);
        });
}

function updatePriceTable(prices) {
    const tableBody = document.querySelector('.table tbody');
    if (!tableBody || !prices || prices.length === 0) {
        return;
    }
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Add new rows
    prices.forEach(price => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${price.date}</td>
            <td>₹${parseFloat(price.price).toFixed(2)}</td>
        `;
        tableBody.appendChild(row);
    });
}

function submitMarketForm() {
    const form = document.querySelector('form');
    if (form) {
        form.submit();
    }
}

function showUpdateNotification(message) {
    // Check if notification element exists
    let notification = document.getElementById('updateNotification');
    
    if (!notification) {
        // Create notification element
        notification = document.createElement('div');
        notification.id = 'updateNotification';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            z-index: 9999;
            animation: slideInRight 0.3s ease;
            font-weight: 600;
        `;
        document.body.appendChild(notification);
    }
    
    notification.textContent = message;
    notification.style.display = 'block';
    
    // Auto-hide after 3 seconds
    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

// Fetch all available crops and populate the dropdown
function loadAvailableCrops() {
    fetch('/api/market/crops')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.crops) {
                const cropSelect = document.getElementById('cropSelect');
                if (cropSelect) {
                    // Get current selection
                    const currentValue = cropSelect.value;
                    
                    // Clear and repopulate options
                    cropSelect.innerHTML = '<option value="">Select a crop...</option>';
                    data.crops.forEach(crop => {
                        const option = document.createElement('option');
                        option.value = crop;
                        option.textContent = crop;
                        if (crop === currentValue) {
                            option.selected = true;
                        }
                        cropSelect.appendChild(option);
                    });
                }
            }
        })
        .catch(error => console.error('Error loading crops:', error));
}

// Load crops on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadAvailableCrops);
} else {
    loadAvailableCrops();
}