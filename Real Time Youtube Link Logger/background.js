let socket = null;
let reconnectInterval = 5000;
let lastSentUrls = new Set();

function connectWebSocket() {
  socket = new WebSocket("ws://localhost:8765");

  socket.onopen = () => {
    console.log("✅ Connected to WebSocket server");
    checkAllTabsForYouTube();
  };

  socket.onclose = () => {
    console.log(`🔌 WebSocket closed. Reconnecting in ${reconnectInterval / 1000}s...`);
    setTimeout(connectWebSocket, reconnectInterval);
  };

  socket.onerror = (error) => {
    console.error("❌ WebSocket error:", error);
    socket.close();
  };

  socket.onmessage = (event) => {
    console.log("📩 Received from server:", event.data);
  };
}

function maybeSendYouTubeUrl(url) {
  const canonicalUrl = getCanonicalYouTubeUrl(url);
  if (!canonicalUrl || lastSentUrls.has(canonicalUrl)) return;

  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ url: canonicalUrl }));
    console.log("📤 Sent URL:", canonicalUrl);
    lastSentUrls.add(canonicalUrl);
  } else {
    console.warn("⚠️ WebSocket not connected. URL not sent:", canonicalUrl);
  }
}

function getCanonicalYouTubeUrl(url) {
  try {
    const parsed = new URL(url);
    if (parsed.hostname.includes("youtube.com") && parsed.pathname === "/watch") {
      const videoId = parsed.searchParams.get("v");
      if (videoId) {
        return `https://www.youtube.com/watch?v=${videoId}`;
      }
    }
  } catch (e) {
    console.error("Invalid URL:", url);
  }
  return null;
}

// Cek semua tab terbuka setelah reconnect
function checkAllTabsForYouTube() {
  browser.tabs.query({})
    .then((tabs) => {
      for (const tab of tabs) {
        if (tab.url && tab.url.includes("youtube.com/watch")) {
          console.log("🔍 Found YouTube tab after reconnect:", tab.url);
          maybeSendYouTubeUrl(tab.url);
        }
      }
    })
    .catch((err) => console.error("Error querying tabs:", err));
}

// Deteksi saat tab di-update (buka YouTube baru)
browser.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === "complete" && tab.url && tab.url.includes("youtube.com/watch")) {
    console.log("🆕 YouTube tab detected:", tab.url);
    maybeSendYouTubeUrl(tab.url);
  }
});

// Inisialisasi koneksi saat extension aktif
connectWebSocket();
