const state = {
    isRunning: true,
    elapsedSeconds: 0,
    currentScore: 0,
    targetScore: 10,
    targetTimeSeconds: 10 * 60, // 10 minutes
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

// --- Utility Functions ---
const formatTime = (totalSeconds) => {
    const hours = Math.floor(totalSeconds / 3600).toString().padStart(2, '0');
    const minutes = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0');
    const seconds = (totalSeconds % 60).toString().padStart(2, '0');
    return `${hours}:${minutes}:${seconds}`;
};

// --- UI Update Functions ---
const updateUI = () => {
    // Timer
    timerEl.textContent = formatTime(state.elapsedSeconds);

    // Score
    scoreDisplay.textContent = state.currentScore;
    scoreProgressText.textContent = `${state.currentScore}/${state.targetScore}`;
    const scorePercent = (state.currentScore / state.targetScore) * 100;
    scoreProgressBar.style.width = `${Math.min(scorePercent, 100)}%`;

    // Time
    const timePercent = (state.elapsedSeconds / state.targetTimeSeconds) * 100;
    timeProgressBar.style.width = `${Math.min(timePercent, 100)}%`;
    timeProgressPercent.textContent = Math.floor(timePercent);
    
    // Check for completion
    if (state.isRunning) {
        if (state.currentScore >= state.targetScore) {
            completeTrial('Target Score Reached');
        } else if (state.elapsedSeconds >= state.targetTimeSeconds) {
            completeTrial('Time Limit Reached');
        }
    }
};

const tick = () => {
    if (!state.isRunning) return;
    state.elapsedSeconds++;
    updateUI();
};

// --- Core Logic ---
const startTrial = () => {
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
};

const stopTrial = () => {};

const completeTrial = (reason) => {};

const fetchTrialStatus = () => {
    if(document.hidden) return; // Don't fetch if the page is hidden (e.g. in another tab)
    fetch('/trial-status')
    .then(response => response.json())
    .then(data => {
        document.getElementById('timeRemaining').textContent = data.timeRemaining;
        document.getElementById('currentIteration').textContent = data.currentIteration;
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
    if (state.isRunning && state.currentScore < state.targetScore) {
        state.currentScore++;
        updateUI();
    }
});

// --- Initialisation ---
startTrial();