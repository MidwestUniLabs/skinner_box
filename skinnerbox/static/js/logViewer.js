onload = function () {
    fetch('/current_user')
        .then(response => response.json())
        .then(data => {
            if (!data.current_user) {
                document.getElementById('remote-logs').style.display = 'none';
                document.getElementById('remote-log-btn').style.display = 'none';
                document.getElementById('local-log-btn').style.display = 'inline-block';
                showToast("Not logged in. Local logs only.", false);
                showLocalLogs();
            } else {
                document.getElementById('remote-logs').style.display = 'block';
                document.getElementById('remote-log-btn').style.display = 'inline-block';
                document.getElementById('local-log-btn').style.display = 'inline-block';
                document.getElementById('local-log-btn').style.backgroundColor = 'transparent';
                showToast("Logged in as: " + data.current_user, true);
                showRemoteLogs();
            }
        })
        .catch(error => console.error('Error fetching current user:', error));
};

function viewRemoteLog(trialInfo) {
    console.log("Viewing trial details:", trialInfo);

    const logViewer = document.getElementById('log-viewer');
    const allLogs = document.querySelectorAll('.log-item');
    allLogs.forEach(log => log.classList.remove('selected'));  // Remove 'selected' class from all items

    const selectedLog = Array.from(allLogs).find(log => log.textContent === new Date(trialInfo.start_time).toLocaleString());
    if (selectedLog) selectedLog.classList.add('selected');

    // Clear existing content
    logViewer.innerHTML = '';

    // Add trial summary details
    const trialSummary = `
        <table>
            <tr><th>Date/Time</th><th>Total Time</th><th>Total Interactions</th></tr>
            <tr>
                <td>${new Date(trialInfo.start_time).toLocaleString()}</td>
                <td>${((new Date(trialInfo.end_time) - new Date(trialInfo.start_time)) / 1000).toFixed(2)}</td>
                <td>${trialInfo.total_interactions}</td>
            </tr>
        </table>
    `;
    logViewer.innerHTML += trialSummary;

    // Add trial entry details
    if (trialInfo.valuesInfoPosition && trialInfo.valuesInfoPosition.length > 0) {
        const trialValuesTable = `
            <table>
                <tr>
                    <th>Entry</th><th>Interaction Time</th><th>Type</th>
                    <th>Reward</th><th>Interactions Between</th><th>Time Between</th>
                </tr>
                ${trialInfo.valuesInfoPosition.map(entry => `
                    <tr>
                        <td>${entry.entry_num}</td>
                        <td>${entry.rel_time}</td>
                        <td>${entry.type}</td>
                        <td>${entry.reward ? 'Yes' : 'No'}</td>
                        <td>${entry.interactions_between}</td>
                        <td>${entry.time_between}</td>
                    </tr>
                `).join('')}
            </table>
        `;
        logViewer.innerHTML += trialValuesTable;
    } else {
        logViewer.innerHTML += '<p>No trial entries available.</p>';
    }
}

function viewLocalLog(filename) {
    console.log(`Fetching local log content for: ${filename}`);
    
    // Highlight selected log
    const allLogs = document.querySelectorAll('.log-item');
    allLogs.forEach(log => log.classList.remove('selected'));
    const selectedLog = Array.from(allLogs).find(log => log.getAttribute('data-filename') === filename);
    if (selectedLog) selectedLog.classList.add('selected');

    // Show buttons
    const rawDownloadBtn = document.getElementById('download-btn');
    const excelDownloadBtn = document.getElementById('download-excel-btn');
    
    // Ensure correct file paths
    rawDownloadBtn.setAttribute("data-filename", filename);
    excelDownloadBtn.setAttribute("data-filename", filename);

    rawDownloadBtn.style.display = 'inline-block';
    excelDownloadBtn.style.display = 'inline-block';
    document.getElementById('push-cloud-btn').style.display = 'inline-block';

    fetch(`/view-log/${encodeURIComponent(filename)}`)
        .then(response => response.json())
        .then(trialInfo => {
            console.log("Viewing local trial details:", trialInfo);
            const logViewer = document.getElementById('log-viewer');
            logViewer.innerHTML = '';

            // Add trial summary details
            const trialSummary = `
                <table>
                    <tr><th>Date/Time</th><th>Total Time</th><th>Total Interactions</th></tr>
                    <tr>
                        <td>${new Date(trialInfo.start_time).toLocaleString()}</td>
                        <td>${((new Date(trialInfo.end_time) - new Date(trialInfo.start_time)) / 1000).toFixed(2)} sec</td>
                        <td>${trialInfo.total_interactions}</td>
                    </tr>
                </table>
            `;
            logViewer.innerHTML += trialSummary;

            // Add trial entry details
            if (trialInfo.trial_entries && trialInfo.trial_entries.length > 0) {
                const trialValuesTable = `
                    <table>
                        <tr>
                            <th>Entry</th><th>Interaction Time</th><th>Type</th>
                            <th>Reward</th><th>Interactions Between</th><th>Time Between</th>
                        </tr>
                        ${trialInfo.trial_entries.map(entry => `
                            <tr>
                                <td>${entry.entry_num}</td>
                                <td>${entry.rel_time.toFixed(2)}</td>
                                <td>${entry.type}</td>
                                <td>${entry.reward ? 'Yes' : 'No'}</td>
                                <td>${entry.interactions_between}</td>
                                <td>${entry.time_between.toFixed(2)}</td>
                            </tr>
                        `).join('')}
                    </table>
                `;
                logViewer.innerHTML += trialValuesTable;
            } else {
                logViewer.innerHTML += '<p>No trial entries available.</p>';
            }
        })
        .catch(error => {
            console.error('Error fetching the log:', error);
            document.getElementById('log-viewer').innerHTML = '<p>Error loading log content.</p>';
        });
}

function showRemoteLogs() {
    const logViewer = document.getElementById('log-viewer');
    logViewer.innerHTML = ''; // Clear existing content
    fetch('/pull_user_logs')
    .then(response => response.json())
    .then(data => {
        const remoteLogsContainer = document.getElementById('remote-logs');
        remoteLogsContainer.innerHTML = ''; // Clear existing content
        console.log('Remote logs data:', data); // Debugging log

        // Sort logs by newest date and time first
        data.data.sort((a, b) => new Date(b.start_time) - new Date(a.start_time));

        data.data.forEach(trial => {
            const trialElement = document.createElement('a');
            trialElement.className = 'log-item';  // Add the log-item class for consistent styling
            trialElement.textContent = new Date(trial.start_time).toLocaleString();
            trialElement.href = "#";  // Prevent page reload
            trialElement.onclick = (event) => {
                event.preventDefault();  // Prevent default link behavior
                viewRemoteLog(trial);
            };
            remoteLogsContainer.appendChild(trialElement);
        });

        })
        .catch(error => {
            console.error('Error fetching remote trials:', error);
            document.getElementById('remote-logs').innerHTML = '<p>Error loading remote logs.</p>';
        });

    document.getElementById('local-logs').style.display = 'none';
    document.getElementById('local-log-btn').style.backgroundColor = 'transparent';
    document.getElementById('remote-logs').style.display = 'block';
    document.getElementById('remote-log-btn').style.backgroundColor = '#6200EE';
    
    document.getElementById('download-btn').style.display = 'none';
    document.getElementById('download-excel-btn').style.display = 'none';
    document.getElementById('push-cloud-btn').style.display = 'none';
}

function showLocalLogs() {
    const logViewer = document.getElementById('log-viewer');

    logViewer.innerHTML = ''; // Clear existing content
    fetch('/list_local_logs')
        .then(response => response.json())
        .then(data => {
            const localLogsContainer = document.getElementById('local-logs');
            localLogsContainer.innerHTML = ''; // Clear existing content

            if (data.log_files.length === 0) {
                const noLogsMessage = document.createElement('p');
                noLogsMessage.textContent = 'No local logs available.';
                noLogsMessage.className = 'no-logs-message';
                document.getElementById('local-logs').appendChild(noLogsMessage);
                return;
            }

            // Sort logs by newest date and time first
            data.log_files.sort((a, b) => {
                const datePartsA = a.replace('log_', '').replace('.json', '').split(/[_\/]/);
                const datePartsB = b.replace('log_', '').replace('.json', '').split(/[_\/]/);

                const yearA = parseInt(datePartsA[2], 10) < 100 ? parseInt(datePartsA[2], 10) + 2000 : parseInt(datePartsA[2], 10);
                const yearB = parseInt(datePartsB[2], 10) < 100 ? parseInt(datePartsB[2], 10) + 2000 : parseInt(datePartsB[2], 10);

                const dateA = new Date(yearA, parseInt(datePartsA[0], 10) - 1, parseInt(datePartsA[1], 10),
                    parseInt(datePartsA[3], 10), parseInt(datePartsA[4], 10), parseInt(datePartsA[5], 10));

                const dateB = new Date(yearB, parseInt(datePartsB[0], 10) - 1, parseInt(datePartsB[1], 10),
                    parseInt(datePartsB[3], 10), parseInt(datePartsB[4], 10), parseInt(datePartsB[5], 10));

                return dateB - dateA;  // Sort newest to oldest
            });

            // Display logs
            data.log_files.forEach(log_file => {
                const logElement = document.createElement('a');
                logElement.className = 'log-item';

                const dateParts = log_file.replace('log_', '').replace('.json', '').split(/[_\/]/);
                const month = parseInt(dateParts[0], 10) - 1;
                const day = parseInt(dateParts[1], 10);
                const year = parseInt(dateParts[2], 10) < 100 ? parseInt(dateParts[2], 10) + 2000 : parseInt(dateParts[2], 10);
                const hours = parseInt(dateParts[3], 10);
                const minutes = parseInt(dateParts[4], 10);
                const seconds = parseInt(dateParts[5], 10);

                const formattedDate = new Date(year, month, day, hours, minutes, seconds).toLocaleString();
                logElement.textContent = formattedDate;
                logElement.setAttribute('data-filename', log_file);
                logElement.href = "#";  // Prevent page reload
                logElement.onclick = function () {
                    console.log(`Clicked log: ${log_file}`);
                    viewLocalLog(log_file);
                };
                localLogsContainer.appendChild(logElement);
            });

            console.log("Local logs loaded:", data.log_files); // Debugging log
        })
        .catch(error => {
            console.error('Error fetching local logs:', error);
            document.getElementById('local-logs').innerHTML = '<p>Error loading local logs.</p>';
        });

    document.getElementById('remote-logs').style.display = 'none';
    document.getElementById('remote-log-btn').style.backgroundColor = 'transparent';
    document.getElementById('local-logs').style.display = 'block';
    document.getElementById('local-log-btn').style.backgroundColor = '#6200EE';

    document.getElementById('download-btn').href = '';
    document.getElementById('download-btn').style.display = 'none';
    document.getElementById('download-excel-btn').href = '';
    document.getElementById('download-excel-btn').style.display = 'none';
    document.getElementById('push-cloud-btn').style.display = 'none';
}

function pushLogToCloud() {
    const filename = document.getElementById('download-btn').getAttribute("data-filename");

    if (!filename) {
        showToast("No log selected to push.", false);
        return;
    }

    console.log(`Pushing log to cloud: ${filename}`);

    const formData = new FormData();
    formData.append("file", filename); // Just send the filename, and let the server handle file retrieval
    formData.append("pi_id", "n4CYyssTN4"); // Replace with the actual pi_id if needed

    fetch('/push_log', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showToast("Failed to push log.", false);
        } else {
            showToast("Log successfully pushed to the cloud!", true);
            document.getElementById('push-cloud-btn').style.display = 'none';
            showLocalLogs(); // Refresh the log list
        }
    })
    .catch(error => {
        console.error('Error pushing log:', error);
        showToast("Failed to push log.", false);
    });
}

function downloadFile(type) {
    const filename = document.getElementById('download-btn').getAttribute("data-filename");

    if (!filename) {
        showToast("No log selected for download.", false);
        return;
    }

    let downloadUrl = "";
    if (type === 'raw') {
        downloadUrl = `/download-raw-log/${encodeURIComponent(filename)}`;
    } else if (type === 'excel') {
        downloadUrl = `/download-excel-log/${encodeURIComponent(filename)}`;
    }

    console.log(`Downloading file from: ${downloadUrl}`);

    // Trigger file download
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast("Download started.", true);
}

function showToast(message, success = true) {
    const toast = document.createElement('div');
    toast.className = `toast ${success ? 'toast-success' : 'toast-error'}`;
    toast.textContent = message;
    document.getElementById('toast-container').appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}