document.getElementById("loginForm").addEventListener("submit", async function (event) {
    event.preventDefault();

    const response = await fetch("/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            email: document.getElementById("emailInput").value,
            password: document.getElementById("passwordInput").value
        })
    });

    if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        window.location.href = "/panel";
    } else {
        alert("Invalid email or password");
    }
});