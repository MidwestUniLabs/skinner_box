document.addEventListener('DOMContentLoaded', () => {
    const statusDisplay = {
        element: document.getElementById('status-display'),
        ping: document.getElementById('status-indicator-ping'),
        dot: document.getElementById('status-indicator-dot'),
        text: document.getElementById('status-text'),
    };

    const statusConfig = {
        Connecting: { text: 'Connecting...', color: 'slate', ping: true, title: 'Attempting to connect to the server...' },
        Running: { text: 'Trial Running', color: 'green', ping: true, title: 'The trial is currently active.' },
        Completed: { text: 'Trial Completed', color: 'emerald', ping: false, title: 'The trial has finished successfully.' },
        ManuallyEnded: { text: 'Trial Ended', color: 'red', ping: false, title: 'The trial was stopped manually.' },
        Stopped: { text: 'Trial Stopped', color: 'red', ping: false, title: 'The trial was stopped manually.' },
        Error: { text: 'Error', color: 'red', ping: false, title: 'An error occurred. Check the logs.' },
        Idle: { text: 'Idle', color: 'slate', ping: false, title: 'The system is idle, awaiting a new trial.' },
        Disconnected: { text: 'Disconnected', color: 'red', ping: false, title: 'Connection to the server was lost.' },
    };

    let currentState = null;
    let fetchInterval;

    const updateStatusUI = (stateKey) => {
        if (stateKey === currentState || !statusConfig[stateKey]) return;
        
        const config = statusConfig[stateKey];
        currentState = stateKey;

        if (statusDisplay.text) statusDisplay.text.textContent = config.text;
        if (statusDisplay.element) statusDisplay.element.title = config.title;

        if (statusDisplay.text) {
            statusDisplay.text.className = `font-semibold text-sm text-${config.color}-400`;
        }
        if (statusDisplay.dot) {
            statusDisplay.dot.className = `relative inline-flex rounded-full h-3 w-3 bg-${config.color}-500`;
        }

        if (statusDisplay.ping) {
            if (config.ping) {
                statusDisplay.ping.classList.remove('hidden');
            } else {
                statusDisplay.ping.classList.add('hidden');
            }
        }
    };

    const fetchTrialStatus = () => {
        fetch('/trial/status')
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.json();
            })
            .then(data => {
                const state = data.state || 'Idle';
                const finalState = data.endStatus ? data.endStatus.replace(/\s/g, '') : state;
                updateStatusUI(finalState);
            })
            .catch(() => {
                updateStatusUI('Disconnected');
            });
    };

    const handleVisibilityChange = () => {
        if (document.hidden) {
            clearInterval(fetchInterval);
        } else {
            fetchTrialStatus();
            fetchInterval = setInterval(fetchTrialStatus, 2000);
        }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    // Initial state
    updateStatusUI('Connecting');
    handleVisibilityChange();
});
