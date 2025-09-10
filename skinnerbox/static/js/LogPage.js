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
        const startTime = new Date(trialInfo.start_time).toLocaleString();
        const totalTime = ((new Date(trialInfo.end_time) - new Date(trialInfo.start_time)) / 1000).toFixed(2);
        
        let entriesHtml = '<p class="mt-4">No trial entries available.</p>';
        const entries = trialInfo.trial_entries || trialInfo.valuesInfoPosition;

        if (entries && entries.length > 0) {
            entriesHtml = `
                <table>
                    <tr>
                        <th>Entry</th><th>Time (s)</th><th>Type</th>
                        <th>Reward</th><th>Interactions Between</th><th>Time Between (s)</th>
                    </tr>
                    ${entries.map(e => `
                        <tr>
                            <td>${e.entry_num}</td>
                            <td>${(e.rel_time || 0).toFixed(2)}</td>
                            <td>${e.type}</td>
                            <td>${e.reward ? 'Yes' : 'No'}</td>
                            <td>${e.interactions_between}</td>
                            <td>${(e.time_between || 0).toFixed(2)}</td>
                        </tr>
                    `).join('')}
                </table>
            `;
        }

        logViewer.innerHTML = `
            <h3 class="text-xl font-semibold text-slate-300 mb-4">Trial Details</h3>
            <table>
                <tr><th>Date/Time</th><th>Total Time (sec)</th><th>Interactions</th></tr>
                <tr><td>${startTime}</td><td>${totalTime}</td><td>${trialInfo.total_interactions}</td></tr>
            </table>
            ${entriesHtml}
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
    fetch('/current_user').then(res => res.json()).then(data => {
        if (data.current_user) {
            showRemoteLogs();
        } else {
            remoteLogBtn.style.display = 'none';
            // Adjust grid to fill space if only one button
            document.querySelector('.log-toggle-group').style.gridTemplateColumns = '1fr';
            showLocalLogs();
        }
    }).catch(err => {
        console.error("Error checking user status:", err);
        showLocalLogs(); // Default to local logs on error
    });
});