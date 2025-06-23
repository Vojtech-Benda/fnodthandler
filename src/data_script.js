    
    
const dataTableBody = document.getElementById("data_table_body");
const ws = new WebSocket(`ws://${location.host}/ws/data`);

const existingIDs = new Set();

ws.onmessage = function(event) {
    console.log("[WebSocket] message received: ", event.data);
    const dataList = JSON.parse(event.data);

    dataList.forEach(item => {
        if (existingIDs.has(item.request_id)) return;
    
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.request_id}</td>
            <td>${item.process_name}</td>
            <td>
                <button class="input_btn action_btn" data_id="${item.request_id}">TXT
                    <i class="fas fa-download"></i>
                    </button>
                    </td>
            <td>
                <button class="output_btn action_btn" data_id="${item.request_id}">ZIP
                    <i class="fas fa-download" title="stáhnout data"></i>
                    </button>(${item.file_size} MB)
                    </td>
        `;
        dataTableBody.appendChild(row);
        existingIDs.add(item.request_id);

    });
};

dataTableBody.addEventListener("click", async (e) => { 
    const request_id = e.target.getAttribute("data_id");
    if (e.target.classList.contains("input_btn")) {
            console.log(`Downloading input data for ${request_id}`);
    } else if (e.target.classList.contains("output_btn")) {
        console.log(`Downloading output data for ${request_id}`);

        try {
            const res = await fetch(`/data-prepare/${request_id}`, {method: "POST"});

            if (!res.ok) {
                console.error("error preparing ZIP file");
                return;
            }

            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = `/data-download/${request_id}`;
            document.body.appendChild(iframe);

        } catch (error) {
            console.error("Download failed: ", error);
        }
    }
});

const idFilter = document.getElementById("request_id_filter");
const processFilter = document.getElementById("process_name_filter");
const tbody = document.getElementById("data_table_body");

function filterTable() {
    const idValue = idFilter.value.toLowerCase();
    const processValue = processFilter.value.toLowerCase();

    Array.from(tbody.rows).forEach(row => {
        const idCell = row.cells[0].textContent.toLowerCase();
        const processCell = row.cells[1].textContent.toLowerCase();

        const matchesId = idCell.includes(idValue);
        const matchesProcess = processCell.includes(processValue);

        row.style.display = (matchesId && matchesProcess) ? "" : "none";
    });
}
    
idFilter.addEventListener("input", filterTable);
processFilter.addEventListener("input", filterTable);
