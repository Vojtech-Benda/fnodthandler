    
    
const dataTableBody = document.getElementById("data_table_body");
const ws = new WebSocket(`ws://${location.host}/ws/data`);

const existingIDs = new Set();

ws.onmessage = function(event) {
    const dataList = JSON.parse(event.data);
    console.log("[WebSocket] message received request_ids: ", dataList.length);
    
    dataList.forEach(item => {
        if (existingIDs.has(item.request_id)) return;
    
        const row = document.createElement("tr");
        row.id = `row_${item.request_id}`;
        row.innerHTML = `
            <td>${item.request_id}</td>
            <td>${item.process_name}</td>
            <td>${item.date}</td>
            <td>${item.finish_time}</td>
            <td>
                <button class="output_btn action_btn" onclick="saveZipFile('${item.request_id}');">ZIP
                    <i class="fas fa-download" title="stáhnout data"></i>
                </button>(${item.file_size} MB)
            </td>

        `;

            // <td>
            //     <button class="delete_btn action_btn" onclick="deleteZipFile('${item.request_id}');">
            //         <i class="fas fa-trash" aria-hidden="true" title="smazat data"></i>
            //     </button>
            // </td>
        dataTableBody.appendChild(row);
        existingIDs.add(item.request_id);

    });
};

async function saveZipFile(request_id) {
    console.log(`Requesting output data for ${request_id}`);

    try {
        const iframe = document.createElement('iframe');
        iframe.style.display = 'none';
        iframe.src = `/data-download/${request_id}`;
        document.body.appendChild(iframe);
    } catch (error) {
        console.error("Download failed: ", error);
    }
};

async function deleteZipFile(request_id) {
    console.log(`Requesting deletion of ${request_id} output data`);

    try {
        const res = await fetch(`/data-delete/${request_id}`, {method: "POST"});

        if (!res.ok) {
            console.error("error deleting ZIP file");
            return;
        }

    } catch (error) {
        console.error("Request for deletion failed: ", error);
    }
};

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
