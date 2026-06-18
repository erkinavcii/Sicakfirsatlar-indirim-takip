document.addEventListener("DOMContentLoaded", () => {
    const scanBtn = document.getElementById("btn-scan");
    const scanBtnText = document.getElementById("scan-btn-text");
    let pollingInterval = null;

    if (scanBtn) {
        scanBtn.addEventListener("click", async () => {
            // Disable button and show spinner
            setScanLoading(true);
            
            try {
                const response = await fetch("/scan", { method: "POST" });
                const result = await response.json();
                
                if (result.status === "success") {
                    // Start polling status
                    startPollingStatus();
                } else {
                    alert("Hata: " + result.message);
                    setScanLoading(false);
                }
            } catch (err) {
                console.error("Scan trigger failed:", err);
                alert("Tarama başlatılamadı.");
                setScanLoading(false);
            }
        });
    }

    // Function to set the button loading state
    function setScanLoading(isLoading) {
        if (isLoading) {
            scanBtn.disabled = true;
            scanBtn.innerHTML = `<i class="fa-solid fa-circle-notch spinner"></i> <span id="scan-btn-text">Taranıyor...</span>`;
        } else {
            scanBtn.disabled = false;
            scanBtn.innerHTML = `<i class="fa-solid fa-magnifying-glass"></i> <span id="scan-btn-text">Şimdi Tara</span>`;
        }
    }

    // Start checking scan status periodically
    function startPollingStatus() {
        if (pollingInterval) clearInterval(pollingInterval);
        
        pollingInterval = setInterval(async () => {
            try {
                const response = await fetch("/scan-status");
                const status = await response.json();
                
                if (!status.running) {
                    clearInterval(pollingInterval);
                    setScanLoading(false);
                    // Reload page to show new deals
                    window.location.reload();
                }
            } catch (err) {
                console.error("Error checking scan status:", err);
            }
        }, 2000);
    }

    // If page is loaded and scan was already running, start polling
    async function checkInitialStatus() {
        try {
            const response = await fetch("/scan-status");
            const status = await response.json();
            if (status.running) {
                setScanLoading(true);
                startPollingStatus();
            }
        } catch (err) {
            console.error("Error checking initial status:", err);
        }
    }

    checkInitialStatus();
});
