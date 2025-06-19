const historyTable = document.getElementById("history_table");
    const ws = new WebSocket(`ws://${location.host}/ws/history`);
    
    ws.onmessage = function(event) {
        const jobs = JSON.parse(event.data);
        historyTable.innerHTML = ""; // clear previous data      
        jobs.forEach(job => {
            const row = document.createElement("tr");
            const status_class = `status_badge status_${job.status}`;
            const status_text = job.status.charAt(0).toUpperCase() + job.status.slice(1);
            const uid_cell_text = job.series_uid_list.join(",<br>")

            row.innerHTML = `
                <td>${job.request_id}</td>
                <td>${job.pacs_ae} ${job.pacs_ip}:${job.pacs_port}</td>
                <td>${job.process_name}</td>
                <td><div class=uid-cell>${uid_cell_text}</div></td>
                <td>${job.notify_email}</td>
                <td>${job.date}</td>
                <td>${job.start_time}</td>
                <td>${job.finish_time}</td>
                <td><span class="status_badge status_${job.status}">${job.status}</span></td>
            `;
            historyTable.appendChild(row);
        });
    };