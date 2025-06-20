const current_job_div = document.getElementById("current_job");
const pending_jobs_table = document.getElementById("pending_jobs");
const ws = new WebSocket(`ws://${location.host}/ws/jobs`);

ws.onmessage = function(event) {
    console.log("[WebSocket] message received:", event.data);
    const data = JSON.parse(event.data);
    const current = data.current_job;
    const pending = data.pending_jobs;

    current_job_div.innerHTML = '';
    pending_jobs_table.innerHTML = '';

    if (current) {
        const current_uid_cell_text = current.uid_list.join(",<br>")
        current_job_div.innerHTML = `
            <div class="job_card_inner">
                <strong>ID:</strong> ${current.request_id}<br>
                <strong>PACS:</strong> ${current.pacs.aetitle} ${current.pacs.ip}:${current.pacs.port}<br>
                <strong>Process:</strong> ${current.process_name}<br>
                <strong>UID:</strong> ${current_uid_cell_text}<br>
                <strong>Email:</strong> ${current.notify_email}<br>
                <strong>Datum vytvoření:</strong> ${current.date}<br>
                <strong>Čas začátku:</strong> ${current.start_time}<br>
                <strong>Čas dokončení:</strong> ${current.finish_time}<br>
                <strong>Status:</strong> <span class="status_badge status_${current.status}">${current.status}</span>
            </div>
        `;
    } else {
        current_job_div.innerHTML = `<p> Žádná aktivní žádost</p>`;
    }

    pending_jobs.innerHTML = '';
    pending.forEach(job => {
        const row = document.createElement('tr');
        const status_class = `status_badge status_${job.status}`;
        const status_text = job.status.charAt(0).toUpperCase() + job.status.slice(1);
        const uid_cell_text = job.uid_list.join(",<br>")

        row.innerHTML = `
            <td>${job.request_id}</td>
            <td>${job.pacs.aetitle} ${job.pacs.ip}:${job.pacs.port}</td>
            <td>${job.process_name}</td>
            <td><div class="uid-cell">${uid_cell_text}</div></td>
            <td>${job.notify_email}</td>
            <td>${job.date}</td>
            <td>${job.start_time}</td>
            <td>${job.finish_time}</td>
            <td><span class="${status_class}">${status_text}</span></td>
        `;
        pending_jobs_table.appendChild(row);
    });
};

document.getElementById("job_form").addEventListener("submit", async function(e) {
    e.preventDefault();  // prevents default from submission

    const formData = new FormData(this);
    for (const [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`)

    }

    try {
        const response = await fetch("/submit", {
            method: "POST",
            body: formData,
            headers: {
                "X-Requested-With": "XMLHttpRequest"
            }
        });

        console.log("Status:", response.status);

        if (!response.ok) throw new Error("Network response was not ok");
        const result = await response.json();
        console.log("Job submitted:", result.message);

        this.reset();
        document.getElementById("job_added_msg").textContent = "Požadavek přidán!";
    } catch (error) {
        console.error("Failed to submit job:", error);
    }
});