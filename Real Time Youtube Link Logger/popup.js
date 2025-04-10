const statusEl = document.getElementById("status");
const toggleBtn = document.getElementById("toggle");

function updateUI(enabled) {
  statusEl.textContent = enabled ? "Enabled" : "Disabled";
  toggleBtn.textContent = enabled ? "Disable" : "Enable";
}

browser.storage.local.get("enabled").then((result) => {
  const enabled = result.enabled === undefined ? true : result.enabled;
  updateUI(enabled);
});

toggleBtn.addEventListener("click", () => {
  browser.storage.local.get("enabled").then((result) => {
    const current = result.enabled === undefined ? true : result.enabled;
    const newStatus = !current;

    browser.storage.local.set({ enabled: newStatus }).then(() => {
      browser.runtime.sendMessage({ type: "toggle", enabled: newStatus });
      updateUI(newStatus);
    });
  });
});
