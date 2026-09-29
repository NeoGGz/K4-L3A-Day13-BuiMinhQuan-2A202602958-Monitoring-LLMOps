// Export the six currently visible dashboard cards without external libraries.
document.getElementById("download-dashboard").addEventListener("click", () => {
  const canvas = document.createElement("canvas");
  canvas.width = 1600;
  canvas.height = 1080;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "#f4f6fa";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  function write(text, x, y, size, color, weight = 400) {
    ctx.font = `${weight} ${size}px system-ui, sans-serif`;
    ctx.fillStyle = color;
    ctx.fillText(text, x, y);
  }

  function wrap(text, x, y, width, size, maxLines = 3) {
    ctx.font = `400 ${size}px system-ui, sans-serif`;
    const words = text.split(/\s+/);
    let line = "";
    let count = 0;
    for (const word of words) {
      const next = line ? `${line} ${word}` : word;
      if (ctx.measureText(next).width > width && line) {
        write(line, x, y + count * 24, size, "#42516a");
        count += 1;
        if (count >= maxLines) return;
        line = word;
      } else {
        line = next;
      }
    }
    if (line && count < maxLines) write(line, x, y + count * 24, size, "#42516a");
  }

  write(document.querySelector("h1").textContent, 48, 58, 30, "#172538", 700);
  write(document.querySelector(".meta").textContent, 48, 88, 16, "#566377");
  document.querySelectorAll(".card").forEach((card, index) => {
    const col = index % 3;
    const row = Math.floor(index / 3);
    const x = 48 + col * 514;
    const y = 122 + row * 460;
    ctx.fillStyle = "#ffffff";
    ctx.beginPath();
    ctx.roundRect(x, y, 490, 432, 14);
    ctx.fill();
    ctx.strokeStyle = "#dfe5ee";
    ctx.stroke();
    write(card.querySelector("h2").textContent, x + 24, y + 38, 19, "#172538", 700);
    write(card.querySelector(".value").textContent, x + 24, y + 92, 32, "#172538", 700);
    wrap(card.querySelector(".details").textContent, x + 24, y + 130, 440, 16);
    const barContainer = card.querySelector(".bars");
    const bars = [...card.querySelectorAll(".bar")];
    const values = bars.map((bar) => Number(bar.title) || 0);
    const peak = Number(barContainer.dataset.scale) || Math.max(...values, 1);
    const barWidth = 438 / bars.length;
    bars.forEach((bar, i) => {
      const height = Math.max(2, (values[i] / peak) * 142);
      ctx.fillStyle = bar.style.backgroundColor || "#5b8def";
      ctx.fillRect(x + 25 + i * barWidth, y + 342 - height, Math.max(2, barWidth - 2), height);
    });
    if (barContainer.dataset.threshold !== "") {
      const lineY = y + 342 - Math.min(0.98, Number(barContainer.dataset.threshold) / peak) * 142;
      ctx.strokeStyle = "#e05b57";
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(x + 24, lineY);
      ctx.lineTo(x + 464, lineY);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.strokeStyle = "#dfe5ee";
    ctx.beginPath();
    ctx.moveTo(x + 24, y + 343);
    ctx.lineTo(x + 464, y + 343);
    ctx.stroke();
    write(card.querySelector(".threshold").textContent, x + 24, y + 388, 15, "#59687a");
  });

  canvas.toBlob((blob) => {
    if (!blob) return;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `11-dashboard-overview-${Date.now()}.png`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }, "image/png");
});
