const token = localStorage.getItem("token");
if (!token) {
    window.location.href = "/login";
}

let currentTicketId = null;
let lastMessageCount = 0;


async function apiFetch(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            ...(options.headers || {}),
            "Authorization": `Bearer ${token}`
        }
    });

    if (response.status === 401 || response.status === 403) {
        localStorage.removeItem("token");
        window.location.href = "/login";
    }
    return response;
}


async function loadTickets() {
    const status = document.getElementById("statusFilter").value;
    const url = status ? `/tickets?status=${status}` : "/tickets";

    const response = await apiFetch(url);
    if (!response.ok) return;
    const tickets = await response.json();

    const list = document.getElementById("ticketsList");
    list.innerHTML = "";

    tickets.forEach(function (t) {
        const item = document.createElement("div");
        item.className = "ticket-item";
        if (t.id === currentTicketId) item.classList.add("active");

        const name = document.createElement("strong");
        name.textContent = t.client_name;

        const meta = document.createElement("span");
        meta.textContent = ` #${t.id}` + (t.client_username ? ` · @${t.client_username}` : "");

        item.appendChild(name);
        item.appendChild(meta);
        item.addEventListener("click", function () {
            openTicket(t);
        });
        list.appendChild(item);
    });
}


async function openTicket(ticket) {
    currentTicketId = ticket.id;
    lastMessageCount = 0;

    document.getElementById("chatTitle").textContent = `${ticket.client_name} · #${ticket.id}`;

    const isOpen = ticket.status === "open";
    document.getElementById("replyForm").classList.toggle("hidden", !isOpen);
    document.getElementById("closeTicketButton").classList.toggle("hidden", !isOpen);

    await loadMessages();
    loadTickets();
}


async function loadMessages() {
    if (currentTicketId === null) return;

    const ticketId = currentTicketId;
    const response = await apiFetch(`/tickets/${ticketId}/messages`);
    if (!response.ok) return;
    const messages = await response.json();

    if (ticketId !== currentTicketId) return;

    if (messages.length === lastMessageCount) return;
    lastMessageCount = messages.length;

    const box = document.getElementById("messagesBox");
    box.innerHTML = "";

    messages.forEach(function (m) {
        const bubble = document.createElement("div");
        bubble.className = `message ${m.sender_type}`;
        bubble.textContent = m.text;
        box.appendChild(bubble);
    });

    box.scrollTop = box.scrollHeight;
}


document.getElementById("replyForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const input = document.getElementById("replyInput");
    const text = input.value.trim();
    if (!text || currentTicketId === null) return;

    const response = await apiFetch(`/tickets/${currentTicketId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: text })
    });

    if (response.ok) {
        input.value = "";
        await loadMessages();
    } else {
        alert("The message was not delivered to Telegram");
    }
});


document.getElementById("closeTicketButton").addEventListener("click", async function () {
    if (currentTicketId === null) return;

    await apiFetch(`/tickets/${currentTicketId}/close`, { method: "PATCH" });
    document.getElementById("replyForm").classList.add("hidden");
    this.classList.add("hidden");
    loadTickets();
});


document.getElementById("statusFilter").addEventListener("change", loadTickets);

document.getElementById("logoutButton").addEventListener("click", function () {
    localStorage.removeItem("token");
    window.location.href = "/login";
});


function connectWebSocket() {
    const protocol = location.protocol === "https:" ? "wss" : "ws";
    const socket = new WebSocket(`${protocol}://${location.host}/ws`);

    socket.addEventListener("open", function () {
        socket.send(token);  
        loadTickets();      
        loadMessages() 
    });

    socket.addEventListener("message", function (event) {
        const data = JSON.parse(event.data);
        loadTickets();

        if (data.ticket_id === currentTicketId) {
            if (data.type === "ticket_closed") {
                document.getElementById("replyForm").classList.add("hidden");
                document.getElementById("closeTicketButton").classList.add("hidden");
            }
            loadMessages();
        }
    });

    socket.addEventListener("close", function (event) {
        if (event.code === 1008) {        
            localStorage.removeItem("token");
            window.location.href = "/login";
            return;
        }
        setTimeout(connectWebSocket, 3000); 
    });
}

loadTickets();
connectWebSocket();