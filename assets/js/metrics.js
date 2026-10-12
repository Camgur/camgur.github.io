(async function () {
  const root = document.getElementById("chemrxiv-metrics");
  if (!root) return;

  const viewsEl = document.getElementById("metric-views");
  const downloadsEl = document.getElementById("metric-downloads");
  const updatedEl = document.getElementById("metrics-updated");

  try {
    const response = await fetch(root.dataset.metricsUrl, {
      cache: "no-store"
    });

    if (!response.ok) {
      throw new Error("Metrics snapshot unavailable");
    }

    const data = await response.json();

    if (data.verified !== true) {
      updatedEl.textContent =
        "Metrics awaiting verification against ChemRxiv.";
      return;
    }

    if (Number.isSafeInteger(data.views) && data.views >= 0) {
      viewsEl.textContent = data.views.toLocaleString();
    }

    if (Number.isSafeInteger(data.downloads) && data.downloads >= 0) {
      downloadsEl.textContent = data.downloads.toLocaleString();
    }

    if (data.updated_at) {
      const date = new Date(data.updated_at);
      const formatted = Number.isNaN(date.getTime())
        ? data.updated_at
        : date.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
            timeZone: "UTC"
          });

      updatedEl.textContent = "ChemRxiv-reported metrics · Updated " + formatted;
    }
  } catch {
    updatedEl.textContent =
      "Metrics temporarily unavailable. Visit ChemRxiv for the preprint.";
  }
})();
