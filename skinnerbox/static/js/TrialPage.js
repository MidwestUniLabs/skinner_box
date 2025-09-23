const state = {
    isRunning: true,
    elapsedSeconds: 0,
    currentScore: 0,
    targetScore: 10,
    targetTimeSeconds: 10 * 60,
    timeRemaining: null,
    backendState: 'Idle',
    timerInterval: null,
    mainInterval: null,
};

// --- DOM Elements ---
const timerEl = document.getElementById('timer');
const forceStopBtn = document.getElementById('force-stop-btn');
const recordPointBtn = document.getElementById('record-point-btn');
const stopModal = document.getElementById('stop-modal');
const modalContent = stopModal.querySelector('.modal-content');
const cancelStopBtn = document.getElementById('cancel-stop-btn');
const confirmStopBtn = document.getElementById('confirm-stop-btn');

const scoreDisplay = document.getElementById('current-score-display');
const scoreProgressText = document.getElementById('current-score-progress');
const scoreProgressBar = document.getElementById('score-progress-bar');
const targetScoreProgressEl = document.getElementById('target-score-progress');

const timeProgressPercent = document.getElementById('time-progress-percent');
const timeProgressBar = document.getElementById('time-progress-bar');
const targetScoreTotalEl = document.getElementById('target-score-total');
const targetScoreLabelEl = document.getElementById('target-score-label');
const targetTimeLabelEl = document.getElementById('target-time-label');

// --- Utility Functions ---
const formatTime = (totalSeconds) => {
    const hours = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const seconds = (totalSeconds % 60).toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
};

// --- UI Update Functions ---
const updateUI = () => {
    // Timer - use elapsed time directly
    const elapsed = state.elapsedSeconds;
    timerEl.textContent = formatTime(elapsed);

    // Score
    scoreDisplay.textContent = state.currentScore;
    scoreProgressText.textContent = state.currentScore;
    const scorePercent = state.targetScore > 0 ? (state.currentScore / state.targetScore) * 100 : 0;
    scoreProgressBar.style.width = `${Math.min(scorePercent, 100)}%`;

    // Time
    const timePercent = state.targetTimeSeconds > 0
        ? (elapsed / state.targetTimeSeconds) * 100
        : 0;
    timeProgressBar.style.width = `${Math.min(timePercent, 100)}%`;
    timeProgressPercent.textContent = Math.floor(timePercent);
    // Completion is driven by backend state only
};

// Removed tick function - now using backend elapsed time

// --- Core Logic ---
const loadConfig = () => {
    return fetch('/trial/config')
        .then(r => r.json())
        .then(cfg => {
            if (cfg && !cfg.error) {
                if (typeof cfg.targetScore === 'number') state.targetScore = cfg.targetScore;
                if (typeof cfg.targetTimeSeconds === 'number') state.targetTimeSeconds = cfg.targetTimeSeconds;
                if (targetScoreTotalEl) targetScoreTotalEl.textContent = state.targetScore;
                if (targetScoreLabelEl) targetScoreLabelEl.textContent = state.targetScore;
                if (targetScoreProgressEl) targetScoreProgressEl.textContent = state.targetScore;
                if (targetTimeLabelEl) {
                    const mm = Math.floor(state.targetTimeSeconds / 60).toString().padStart(2, '0');
                    const ss = (state.targetTimeSeconds % 60).toString().padStart(2, '0');
                    targetTimeLabelEl.textContent = `${mm}:${ss}`;
                }
            }
        })
        .catch(() => {});
};

const startTrial = async () => {
    await loadConfig();
    state.isRunning = true;
    // No need for timer interval - backend provides elapsed time
    updateUI();
};

const endTrial = () => {
    if (!state.isRunning) return;
    state.isRunning = false;
    clearInterval(state.mainInterval);

    forceStopBtn.disabled = true;
    if (recordPointBtn) recordPointBtn.disabled = true;
};

const stopTrial = () => {
    // Create a form and submit it to navigate to the manuallyEndTrial route
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/manuallyEndTrial';
    document.body.appendChild(form);
    form.submit();
};

const completeTrial = () => {
    endTrial();
};

const fetchTrialStatus = () => {
    if(document.hidden) return; // Don't fetch if the page is hidden (e.g. in another tab)
    fetch('/trial/status')
    .then(response => response.json())
    .then(data => {
        const timeRemainingEl = document.getElementById('timeRemaining');
        const currentIterationEl = document.getElementById('currentIteration');
        if (typeof data.currentIteration === 'number') {
            state.currentScore = data.currentIteration;
        }
        if (typeof data.timeRemaining === 'number') {
            state.timeRemaining = data.timeRemaining;
        }
        if (typeof data.elapsedTime === 'number') {
            state.elapsedSeconds = Math.floor(data.elapsedTime);
        }
        if (typeof data.state === 'string') {
            state.backendState = data.state;
        }
        if (timeRemainingEl) timeRemainingEl.textContent = (typeof state.timeRemaining === 'number') ? Math.round(state.timeRemaining) : '';
        if (currentIterationEl) currentIterationEl.textContent = state.currentScore ?? '';
        updateUI();
        if (state.isRunning && data && (data.state === 'Completed' || data.state === 'Stopped' || data.state === 'Error')) {
            if (data.state === 'Completed') {
                completeTrial();
            } else {
                endTrial();
            }
        }
    })
    .catch(error => console.error('Error fetching trial status:', error));

}

const checkCompletion = () => {
    if (document.hidden) return;
    fetch('/trial/check_completion')
        .then(response => response.json())
        .then(data => {
            if (data.completed && data.log_file) {
                // Construct the URL for the log viewer page with the log file as a query parameter
                const logFile = encodeURIComponent(data.log_file.split('/').pop());
                window.location.href = `/log-viewer?file=${logFile}`;
            }
        })
        .catch(error => console.error('Error checking trial completion:', error));
};

const handleVisibilityChange = () => {
    if (document.hidden) {
        clearInterval(state.mainInterval);
    } else if (state.isRunning) {
        // Run once on visibility change, then set interval
        fetchTrialStatus();
        checkCompletion();
        state.mainInterval = setInterval(() => {
            fetchTrialStatus();
            if (state.isRunning) {
                checkCompletion();
            }
        }, 1000);
    }
};

document.addEventListener('visibilitychange', handleVisibilityChange);

// --- Modal Logic ---
const openModal = () => {
    stopModal.classList.remove('pointer-events-none');
    stopModal.classList.add('opacity-100');
    modalContent.classList.add('scale-100', 'opacity-100');
    modalContent.classList.remove('scale-95', 'opacity-0');
};

const closeModal = () => {
    modalContent.classList.remove('scale-100', 'opacity-100');
    modalContent.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
        stopModal.classList.add('pointer-events-none');
        stopModal.classList.remove('opacity-100');
    }, 300);
};

// --- Event Listeners ---
forceStopBtn.addEventListener('click', openModal);
cancelStopBtn.addEventListener('click', closeModal);
confirmStopBtn.addEventListener('click', () => {
    stopTrial();
    closeModal();
});

if (recordPointBtn) {
    recordPointBtn.addEventListener('click', () => {
        if (!state.isRunning) return;
        fetch('/trial/record', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                if (data && !data.error) {
                    // Keep UI score in sync with backend iteration if provided
                    if (typeof data.currentIteration === 'number') {
                        state.currentScore = data.currentIteration;
                    } else {
                        state.currentScore += 1;
                    }
                    updateUI();
                }
            })
            .catch(() => {
                // Fallback to local increment
                state.currentScore += 1;
                updateUI();
            });
    });
}

// --- Initialisation ---
startTrial().then(() => {
    // Initial run
    handleVisibilityChange();
});