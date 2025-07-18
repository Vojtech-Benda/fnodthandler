const current_job_div = document.getElementById("current_job");
const pending_jobs_table = document.getElementById("pending_jobs");
const uidFileupBtn = document.getElementById("uid_fileup_btn");
uidFileupBtn.addEventListener("change", updateUidTextArea);
const ws = new WebSocket(`ws://${location.host}/ws/jobs`);

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log("[WebSocket] message received:", data.request_id);
    const current = data.current_job;
    const pending = data.pending_jobs || [];

    current_job_div.innerHTML = '';
    pending_jobs_table.innerHTML = '';


    // <div class="card_row">${current_uid_cell_text}</div>
    // <div class="card_row">${current.finish_time}</div>
    if (current) {
        const current_uid_cell_text = current.uid_list.join(",<br>");
        current_job_div.innerHTML = `
                <div class="card_row"><strong>ID požadavku:</strong>${current.request_id}</div>
                <div class="card_row"><strong>PACS:</strong>${current.pacs.aetitle} ${current.pacs.ip}:${current.pacs.port}</div>
                <div class="card_row"><strong>Proces:</strong>${current.process_name}</div>
                <div class="card_row"><strong>Email:</strong>${current.notify_email}</div>
                <div class="card_row"><strong>Datum:</strong>${current.date}</div>
                <div class="card_row"><strong>Čas začátku:</strong>${current.start_time}</div>
                <div class="card_row"><span class="status_badge status_${current.status}">${current.status}</span></div>
            
        `;
        // current_job_div.innerHTML = `
        //         <div class="card_row"><strong>ID požadavku:</strong>a1b2c3d4e5</div>
        //         <div class="card_row"><strong>PACS:</strong>ORTHANC 192.168.100.100:2000</div>
        //         <div class="card_row"><strong>Proces:</strong>konverze dcm2mha</div>
        //         <div class="card_row"><strong>Datum:</strong>20-11-2025</div>
        //         <div class="card_row"><strong>Čas začátku:</strong>19:20:50</div>
        //         <div class="card_row"><span class="status_badge status_done">done</span></div>
        // `;
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
    const knownKeys = ["pacs_select", "process_select", "notify_email", "uid_list"]
    for (const [key, value] of formData.entries()) {
        console.log(`${key}: ${value}`)

    }

    const payload = {};
    const additionalOptions = {};

    for (const [key, value] of formData.entries()) {
        if (knownKeys.includes(key)) {
            payload[key] = value;
        } else {
            additionalOptions[key] = value;
        }
    }
    payload.additional_options = additionalOptions;

    try {
        const response = await fetch("/submit", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest"
            },
            body: JSON.stringify(payload),
        });

        console.log("Status:", response.status);

        if (!response.ok) throw new Error("Network response was not ok");
        const result = await response.json();
        console.log("Job submitted:", result.message);

        this.reset();
        // document.getElementById("job_added_msg").textContent = "Požadavek přidán!";
    } catch (error) {
        console.error("Failed to submit job:", error);
    }
});


function updateUidTextArea(event) {
    const uidListTextarea = document.getElementById("uid_list");
    uidListTextarea.textContent = "";

    const file = event.target.files[0];

    const reader = new FileReader();
    reader.onload = () => {
        uidListTextarea.textContent = reader.result;
    };
    reader.onerror = () => {
        console.log("error reading file");
    };

    reader.readAsText(file);
};

document.getElementById('open_modal_btn').addEventListener('click', function() {
    document.getElementById('job_modal').style.display = 'block';
});

document.getElementById('close_modal_btn').addEventListener('click', function () {
    document.getElementById('job_modal').style.display = 'none';
});

window.addEventListener('click', function(event) {
    const modal = this.document.getElementById('job_modal')
    if (event.target == modal) {
        modal.style.display = 'none'
    }
});

const additionalOptionsToggleBtn = document.getElementById("toggle_options_btn");
const optionsContainer = document.getElementById("div_addit_process_options");
const processSelector = document.getElementById("process_select")

let expanded = false;

additionalOptionsToggleBtn.addEventListener('click', () => {
    expanded = !expanded;
    optionsContainer.style.display = expanded ? 'flex' : 'none';
    additionalOptionsToggleBtn.textContent = expanded ? '▼ Nastavení procesu' : '▶ Nastavení procesu';
});

processSelector.addEventListener('change', async () => {
    const value = processSelector.value;
    if (!value) {
        additionalOptionsToggleBtn.click();
        optionsContainer.innerHTML = ``;
        optionsContainer.style = "";
        return;
    }
    
    if (!expanded) additionalOptionsToggleBtn.click();

    try {
        const response = await fetch(`/process_options/${value}.html`);
        if (!response.ok) throw new Error(`failed to load options ${value}`);

        const html = await response.text();
        optionsContainer.innerHTML = html;
    } catch (err) {
        optionsContainer.innerHTML = `<p style="color: red;">Unable to load options for "${value}".</p>`;
        console.error(err);
    }
});