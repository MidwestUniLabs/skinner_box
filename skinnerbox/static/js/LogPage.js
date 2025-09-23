document.addEventListener('DOMContentLoaded', () => {
    const remoteLogBtn = document.getElementById('remote-log-btn');
    const localLogBtn = document.getElementById('local-log-btn');
    const remoteLogsContainer = document.getElementById('remote-logs');
    const localLogsContainer = document.getElementById('local-logs');
    const actionButtons = document.getElementById('action-buttons');
    const downloadBtn = document.getElementById('download-btn');
    const downloadExcelBtn = document.getElementById('download-excel-btn');
    const pushCloudBtn = document.getElementById('push-cloud-btn');
    const logViewer = document.getElementById('log-viewer');
    
    let selectedLocalLog = null;

    // --- Core Functions ---

    const setActiveToggle = (activeBtn) => {
        [remoteLogBtn, localLogBtn].forEach(btn => btn.classList.remove('active'));
        activeBtn.classList.add('active');
    };

    const showLocalLogs = () => {
        setActiveToggle(localLogBtn);
        remoteLogsContainer.style.display = 'none';
        localLogsContainer.style.display = 'block';
        
        fetch('log-viewer/list-local').then(res => res.json()).then(data => {
            localLogsContainer.innerHTML = '';
            if (!data.log_files || data.log_files.length === 0) {
                localLogsContainer.innerHTML = `<p class="no-logs-message">No local logs found.</p>`;
                return;
            }
            
            // Sort by date from filename, newest first
            data.log_files.sort((a, b) => b.localeCompare(a)).forEach(filename => {
                const el = document.createElement('a');
                el.className = 'log-item';
                // Extract and format date from a filename like 'log_MM_DD_YY_HH_MM_SS.json'
                const match = filename.match(/(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})_(\d{2})/);
                if (match) {
                    const [, M, D, Y, h, m, s] = match;
                    el.textContent = new Date(`20${Y}-${M}-${D}T${h}:${m}:${s}`).toLocaleString();
                } else {
                    el.textContent = filename;
                }
                el.href = '#';
                el.dataset.filename = filename; // Add this line
                el.onclick = (e) => {
                    e.preventDefault();
                    viewLocalLog(filename, el);
                };
                localLogsContainer.appendChild(el);
            });
        }).catch(err => {
            console.error("Error fetching local logs:", err);
            localLogsContainer.innerHTML = `<p class="no-logs-message">Error loading logs.</p>`;
        });
    };

    const showRemoteLogs = () => {
        setActiveToggle(remoteLogBtn);
        localLogsContainer.style.display = 'none';
        actionButtons.style.display = 'none';
        remoteLogsContainer.style.display = 'block';
        
        fetch('log-viewer/pull-logs').then(res => res.json()).then(data => {
            remoteLogsContainer.innerHTML = '';
            if (!data.data || data.data.length === 0) {
                remoteLogsContainer.innerHTML = `<p class="no-logs-message">No remote logs found.</p>`;
                return;
            }
            data.data.sort((a, b) => new Date(b.start_time) - new Date(a.start_time)).forEach(trial => {
                const el = document.createElement('a');
                el.className = 'log-item';
                el.textContent = new Date(trial.start_time).toLocaleString();
                el.href = '#';
                el.onclick = (e) => {
                    e.preventDefault();
                    viewRemoteLog(trial, el);
                };
                remoteLogsContainer.appendChild(el);
            });
        }).catch(err => {
            console.error("Error fetching remote logs:", err);
            remoteLogsContainer.innerHTML = `<p class="no-logs-message">Error loading logs.</p>`;
        });
    };

    const renderLogDetails = (trialInfo) => {
        const {
            pi_id = 'N/A',
            status = 'N/A',
            start_time = 'N/A',
            end_time = 'N/A',
            total_interactions = 0,
            total_rewards = 0,
            total_no_reward = 0,
            counts_by_type = {},
            trial_entries = [],
        } = trialInfo;

        const duration = (new Date(end_time) - new Date(start_time)) / 1000;
        const duration_display = isNaN(duration) ? 'N/A' : `${duration.toFixed(2)}s`;

        const countsByTypeHtml = Object.entries(counts_by_type).map(([key, value]) => `
            <div class="bg-slate-800/60 p-3 rounded border border-slate-700">
                <p class="text-slate-400 text-sm">${key}</p>
                <p class="text-white text-lg">${value}</p>
            </div>
        `).join('');

        const entriesHtml = trial_entries.length > 0 ? `
            <div class="overflow-x-auto">
                <h3 class="text-lg font-semibold text-white mb-2">Entries</h3>
                <table class="min-w-full text-sm text-left text-slate-300">
                    <thead class="text-xs uppercase bg-slate-800/60 text-slate-400">
                        <tr>
                            <th class="px-4 py-2">#</th>
                            <th class="px-4 py-2">Rel Time</th>
                            <th class="px-4 py-2">Type</th>
                            <th class="px-4 py-2">Reward</th>
                            <th class="px-4 py-2">Interactions Between</th>
                            <th class="px-4 py-2">Time Between</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${trial_entries.map(e => `
                            <tr class="border-b border-slate-800">
                                <td class="px-4 py-2 font-mono">${e.entry_num}</td>
                                <td class="px-4 py-2 font-mono">${(e.rel_time || 0).toFixed(2)}</td>
                                <td class="px-4 py-2">${e.type}</td>
                                <td class="px-4 py-2">${e.reward ? 'Yes' : 'No'}</td>
                                <td class="px-4 py-2 font-mono">${e.interactions_between}</td>
                                <td class="px-4 py-2 font-mono">${(e.time_between || 0).toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        ` : '<p class="mt-4">No trial entries available.</p>';

        logViewer.innerHTML = `
            <div class="lg:col-span-2 bg-slate-900/50 p-6 rounded-lg border border-slate-700">
                <h1 class="text-2xl font-bold text-white mb-4">Trial Summary</h1>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Pi ID</h3>
                        <p class="text-white">${pi_id}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Status</h3>
                        <p class="text-white">${status}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Start Time</h3>
                        <p class="text-white">${new Date(start_time).toLocaleString()}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">End Time</h3>
                        <p class="text-white">${new Date(end_time).toLocaleString()}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Duration</h3>
                        <p class="text-white">${duration_display}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Total Interactions</h3>
                        <p class="text-white">${total_interactions}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">Rewards</h3>
                        <p class="text-white">${total_rewards}</p>
                    </div>
                    <div class="bg-slate-800/60 p-4 rounded border border-slate-700">
                        <h3 class="text-slate-400 text-sm">No Reward</h3>
                        <p class="text-white">${total_no_reward}</p>
                    </div>
                </div>

                <div class="mb-6">
                    <h3 class="text-lg font-semibold text-white mb-2">Counts by Type</h3>
                    <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                        ${countsByTypeHtml}
                    </div>
                </div>

                ${entriesHtml}
            </div>
        `;
    };
    
    const viewLocalLog = (filename, selectedElement) => {
        document.querySelectorAll('.log-item').forEach(el => el.classList.remove('selected'));
        selectedElement.classList.add('selected');
        selectedLocalLog = filename;
        actionButtons.style.display = 'flex';

        fetch(`/log-viewer/view-log/${encodeURIComponent(filename)}`)
            .then(res => res.json())
            .then(renderLogDetails)
            .catch(err => console.error('Error fetching local log:', err));
    };
    
    const viewRemoteLog = (trialInfo, selectedElement) => {
        document.querySelectorAll('.log-item').forEach(el => el.classList.remove('selected'));
        selectedElement.classList.add('selected');
        actionButtons.style.display = 'none';
        renderLogDetails(trialInfo);
    };

    const showToast = (message, success = true) => {
        const toastContainer = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${success ? 'toast-success' : 'toast-error'}`;
        toast.style.cssText = `
            background-color: ${success ? 'var(--color-success)' : 'var(--color-danger)'};
            color: var(--bg-primary);
            padding: 1rem 1.5rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            opacity: 1;
            transition: opacity 0.5s ease;
            pointer-events: auto;
        `;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    };

    // --- Event Listeners ---

    remoteLogBtn.addEventListener('click', showRemoteLogs);
    localLogBtn.addEventListener('click', showLocalLogs);

    downloadBtn.addEventListener('click', () => {
        if (!selectedLocalLog) return;
        window.location.href = `/log-viewer/download-raw/${encodeURIComponent(selectedLocalLog)}`;
    });
    
    downloadExcelBtn.addEventListener('click', () => {
        if (!selectedLocalLog) return;
        window.location.href = `/log-viewer/download-excel/${encodeURIComponent(selectedLocalLog)}`;
    });

    pushCloudBtn.addEventListener('click', () => {
        if (!selectedLocalLog) return;
        const formData = new FormData();
        formData.append("file", selectedLocalLog);
        
        fetch('log-viewer/push-log', { method: 'POST', body: formData })
            .then(res => res.json())
            .then(data => {
                showToast(data.error ? "Failed to push log." : "Log pushed successfully!", !data.error);
                if (!data.error) showLocalLogs();
            })
            .catch(err => {
                console.error('Error pushing log:', err);
                showToast("Failed to push log.", false);
            });
    });

    // --- Initial Load Logic ---
    const initialLoad = () => {
        fetch('/current_user').then(res => res.json()).then(data => {
            if (data.current_user) {
                showRemoteLogs();
            } else {
                remoteLogBtn.style.display = 'none';
                document.querySelector('.log-toggle-group').style.gridTemplateColumns = '1fr';
                showLocalLogs();
            }

            // If a log file is pre-selected (e.g., from a redirect),
            // wait for the log list to populate, then click it.
            if (typeof SELECTED_LOG_FILE !== 'undefined' && SELECTED_LOG_FILE) {
                const observer = new MutationObserver((mutations, obs) => {
                    const logItems = localLogsContainer.querySelectorAll('.log-item');
                    for (let item of logItems) {
                        if (item.textContent.includes(SELECTED_LOG_FILE) || item.dataset.filename === SELECTED_LOG_FILE) {
                            item.click();
                            obs.disconnect(); // Stop observing once found
                            return;
                        }
                    }
                });
                observer.observe(localLogsContainer, { childList: true, subtree: true });
            }
        }).catch(err => {
            console.error("Error checking user status:", err);
            showLocalLogs(); // Default to local logs on error
        });
    };

    initialLoad();
});