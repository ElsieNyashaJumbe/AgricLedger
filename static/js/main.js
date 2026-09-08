// AgricLedger Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('🌾 AgricLedger loaded successfully!');
    
    // Check backend health
    fetch('/api/health')
        .then(response => response.json())
        .then(data => {
            console.log('✅ Backend status:', data);
        })
        .catch(error => {
            console.warn('⚠️ Backend not reachable:', error);
        });
});