function fetchTrialStatus() {
    if(document.hidden) return; // Don't fetch if the page is hidden (e.g. in another tab)
    fetch('/trial-status')
    .then(response => response.json())
    .then(data => {
        document.getElementById('timeRemaining').textContent = data.timeRemaining;
        document.getElementById('currentIteration').textContent = data.currentIteration;
    })
    .catch(error => console.error('Error fetching trial status:', error));
}

// Fetch trial status every second
setInterval(fetchTrialStatus, 100);