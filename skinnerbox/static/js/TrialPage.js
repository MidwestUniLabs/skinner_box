const state = {
    isRunning: true,
    elapsedSeconds: 0,
    currentScore: 0,
    targetScore: 10,
    targetTimeSeconds: 10 * 60,
    timeRemaining: null,
    backendState: 'Idle',
    timerInterval: null,
};

// --- DOM Elements ---
const timerEl = document.getElementById('timer');
const statusDisplay = {
    ping: document.getElementById('status-indicator-ping'),
    dot: document.getElementById('status-indicator-dot'),
    text: document.getElementById('status-text'),
};
const forceStopBtn = document.getElementById('force-stop-btn');
const recordPointBtn = document.getElementById('record-point-btn');
const stopModal = document.getElementById('stop-modal');
const modalContent = stopModal.querySelector('.modal-content');
const cancelStopBtn = document.getElementById('cancel-stop-btn');
const confirmStopBtn = document.getElementById('confirm-stop-btn');

const scoreDisplay = document.getElementById('current-score-display');
const scoreProgressText = document.getElementById('current-score-progress');
const scoreProgressBar = document.getElementById('score-progress-bar');

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
    // Timer (prefer backend-derived elapsed if available and valid)
    const canUseBackendElapsed = (
        state.targetTimeSeconds > 0 &&
        typeof state.timeRemaining === 'number' &&
        state.timeRemaining <= state.targetTimeSeconds &&
        (
            (state.backendState === 'Running' && state.timeRemaining > 0) ||
            (state.backendState === 'Completed' && state.timeRemaining >= 0)
        )
    );

    const elapsed = canUseBackendElapsed
        ? Math.max(0, state.targetTimeSeconds - state.timeRemaining)
        : state.elapsedSeconds;
    timerEl.textContent = formatTime(elapsed);

    // Score
    scoreDisplay.textContent = state.currentScore;
    scoreProgressText.textContent = `${state.currentScore}/${state.targetScore}`;
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

const tick = () => {
    if (!state.isRunning) return;
    // Fallback timer only, backend will override via timeRemaining when available
    state.elapsedSeconds++;
    updateUI();
};

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
    state.timerInterval = setInterval(tick, 1000);
    updateUI();
};

const endTrial = (reason, statusClass, color) => {
    if (!state.isRunning) return;
    state.isRunning = false;
    clearInterval(state.timerInterval);
    
    statusDisplay.text.textContent = reason;
    statusDisplay.text.className = `font-semibold text-sm ${statusClass}`;
    statusDisplay.dot.className = `relative inline-flex rounded-full h-3 w-3 ${color}`;
    statusDisplay.ping.classList.add('hidden');
    
    forceStopBtn.disabled = true;
    recordPointBtn.disabled = true;
    // Redirect to summary page after a short delay
    setTimeout(() => {
        window.location.href = '/summary_page';
    }, 800);
};

const stopTrial = () => {
    fetch('/trial/stop', { method: 'POST' })
        .then(() => {
            endTrial('Stopped Manually', 'text-rose-400', 'bg-rose-500');
        })
        .catch(() => {
            endTrial('Stopped Manually', 'text-rose-400', 'bg-rose-500');
        });
};

const completeTrial = (reason) => {
    endTrial(reason, 'text-emerald-400', 'bg-emerald-500');
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
        if (typeof data.state === 'string') {
            state.backendState = data.state;
        }
        if (timeRemainingEl) timeRemainingEl.textContent = (typeof state.timeRemaining === 'number') ? state.timeRemaining : '';
        if (currentIterationEl) currentIterationEl.textContent = state.currentScore ?? '';
        updateUI();
        if (data && data.state === 'Completed' && data.endStatus) {
            completeTrial(data.endStatus);
        }
    })
    .catch(error => console.error('Error fetching trial status:', error));

}

setInterval(fetchTrialStatus, 1000);

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

// --- Initialisation ---
startTrial();