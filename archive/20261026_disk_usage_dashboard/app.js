const refreshButton = document.querySelector("#refresh");
const statusText = document.querySelector("#status");
const diskContainer = document.querySelector("#disks");
let refreshing = false;
let networkRefreshing = false;

function formatRate(bytesPerSecond) {
  const units = ["B/s", "KiB/s", "MiB/s"];
  const index = bytesPerSecond >= 1024 ** 2 ? 2 : bytesPerSecond >= 1024 ? 1 : 0;
  return `${(bytesPerSecond / 1024 ** index).toLocaleString("zh-CN", { maximumFractionDigits: 1 })} ${units[index]}`;
}

async function refreshNetwork() {
  if (networkRefreshing) return;
  networkRefreshing = true;
  const networkStatus = document.querySelector("#network-status");
  const upload = document.querySelector("#upload-speed");
  const download = document.querySelector("#download-speed");
  try {
    const response = await fetch("/api/network", { cache: "no-store", signal: AbortSignal.timeout(3000) });
    if (!response.ok) throw new Error("读取失败");
    const data = await response.json();
    networkStatus.classList.remove("error");
    if (data.available) {
      upload.textContent = formatRate(data.upload_bytes_per_second);
      download.textContent = formatRate(data.download_bytes_per_second);
      const time = new Date(data.updated_at).toLocaleTimeString("zh-CN", { hour12: false });
      networkStatus.textContent = `网速更新 ${time}`;
    } else {
      upload.textContent = download.textContent = "—";
      networkStatus.textContent = data.message;
    }
  } catch {
    upload.textContent = download.textContent = "—";
    networkStatus.textContent = "网速刷新失败，请确认本地服务正在运行，将自动重试。";
    networkStatus.classList.add("error");
  } finally {
    networkRefreshing = false;
  }
}

function formatSize(bytes) {
  const useTiB = bytes >= 1024 ** 4;
  const value = bytes / 1024 ** (useTiB ? 4 : 3);
  return `${value.toLocaleString("zh-CN", { maximumFractionDigits: 1 })} ${useTiB ? "TiB" : "GiB"}`;
}

function createDiskCard(disk) {
  const card = document.createElement("article");
  card.className = `disk-card ${disk.drive === "C:" ? "drive-c" : "drive-d"}`;
  const title = disk.drive === "C:" ? "C 盘" : "D 盘";
  const percent = disk.available && disk.total > 0 ? (disk.used / disk.total) * 100 : 0;
  const level = percent >= 90 ? "空间紧张" : "空间充足";

  card.innerHTML = `
    <div class="disk-header">
      <div class="disk-identity">
        <span class="disk-icon" aria-hidden="true">${disk.drive}</span>
        <div><h3>${title}</h3><p>本地磁盘</p></div>
      </div>
      <span class="disk-badge ${!disk.available ? "unavailable" : percent >= 90 ? "low-space" : ""}">
        ${disk.available ? level : "暂不可用"}
      </span>
    </div>`;

  if (!disk.available) {
    const message = document.createElement("p");
    message.className = "unavailable-message";
    message.textContent = disk.message;
    card.append(message);
    return card;
  }

  card.insertAdjacentHTML("beforeend", `
    <div class="usage-heading"><strong>${percent.toFixed(1)}<span>%</span></strong><span>已使用</span></div>
    <div class="usage-bar ${percent >= 90 ? "low-space" : ""}" role="progressbar"
      aria-label="${title}已用空间" aria-valuenow="${percent.toFixed(1)}" aria-valuemin="0" aria-valuemax="100">
      <span style="width: ${percent}%"></span>
    </div>
    <div class="usage-legend"><span><i class="used-dot"></i>已用 ${formatSize(disk.used)}</span><span><i class="free-dot"></i>剩余 ${formatSize(disk.free)}</span></div>
    <div class="disk-capacity"><span>磁盘总容量</span><strong>${formatSize(disk.total)}</strong></div>`);
  return card;
}

async function refresh() {
  if (refreshing) return;
  refreshing = true;
  refreshButton.disabled = true;
  refreshButton.textContent = "刷新中…";

  try {
    const response = await fetch("/api/disks", { cache: "no-store" });
    if (!response.ok) throw new Error("读取失败");
    const data = await response.json();
    const available = data.disks.filter((disk) => disk.available);
    for (const key of ["total", "used", "free"]) {
      document.querySelector(`#${key}`).textContent = available.length
        ? formatSize(available.reduce((sum, disk) => sum + disk[key], 0))
        : "—";
    }
    document.querySelector("#drive-count").textContent = `${available.length} / 2 个磁盘可读取`;
    diskContainer.replaceChildren(...data.disks.map(createDiskCard));
    const time = new Date(data.updated_at).toLocaleTimeString("zh-CN", { hour12: false });
    statusText.textContent = `最近更新 ${time}`;
    statusText.classList.remove("error");
  } catch {
    statusText.textContent = "刷新失败，请确认本地服务正在运行。已显示的数据可能已过期，将自动重试。";
    statusText.classList.add("error");
  } finally {
    refreshing = false;
    refreshButton.disabled = false;
    refreshButton.innerHTML = '立即刷新 <span aria-hidden="true">↻</span>';
  }
}

refreshButton.addEventListener("click", () => {
  refresh();
  refreshNetwork();
});
refresh();
refreshNetwork();
setInterval(refresh, 5000);
setInterval(refreshNetwork, 1000);
