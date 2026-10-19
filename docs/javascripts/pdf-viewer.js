// Loaded as an ES module; .js also gets the correct MIME type on Windows previews.
let library;
function pdfLibrary() {
  if (!library) library = import("https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.min.mjs").then(pdfjs => {
    pdfjs.GlobalWorkerOptions.workerSrc = "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/build/pdf.worker.min.mjs";
    return pdfjs;
  }).catch(error => { library = null; throw error; });
  return library;
}

async function preview(attachment) {
  const host = attachment.querySelector(".pdf-preview");
  const status = attachment.querySelector(".pdf-status");
  try {
    const pdfjs = await pdfLibrary();
    const pdf = await pdfjs.getDocument({
      url: attachment.dataset.pdfSrc,
      cMapUrl: "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/cmaps/",
      cMapPacked: true,
      standardFontDataUrl: "https://cdn.jsdelivr.net/npm/pdfjs-dist@4.10.38/standard_fonts/",
      isEvalSupported: false
    }).promise;
    const controls = document.createElement("div"); controls.className = "pdf-controls";
    const prev = document.createElement("button"), next = document.createElement("button"), label = document.createElement("span");
    prev.type = next.type = "button";
    prev.textContent = "← 上一页"; next.textContent = "下一页 →";
    prev.setAttribute("aria-label", "PDF 上一页"); next.setAttribute("aria-label", "PDF 下一页");
    label.setAttribute("aria-live", "polite");
    controls.append(prev, label, next);
    const canvas = document.createElement("canvas");
    canvas.setAttribute("role", "img");
    host.prepend(controls); host.append(canvas);
    let current = 1, revision = 0, task, resizeTimer;
    async function render() {
      const ticket = ++revision;
      if (task) { task.cancel(); await task.promise.catch(() => {}); }
      prev.disabled = next.disabled = true;
      status.hidden = false; status.textContent = "正在渲染第 " + current + " 页……";
      try {
        const page = await pdf.getPage(current);
        if (ticket !== revision) return;
        const original = page.getViewport({scale: 1});
        const scale = Math.max(120, host.clientWidth - 24) / original.width;
        const viewport = page.getViewport({scale});
        const density = Math.min(devicePixelRatio || 1, 2);
        canvas.width = Math.floor(viewport.width * density); canvas.height = Math.floor(viewport.height * density);
        canvas.style.width = viewport.width + "px";
        canvas.setAttribute("aria-label", `PDF 第 ${current} 页，共 ${pdf.numPages} 页；可通过上方链接打开完整原文件。`);
        task = page.render({canvasContext: canvas.getContext("2d"), viewport, transform: density === 1 ? null : [density,0,0,density,0,0]});
        await task.promise;
        if (ticket !== revision) return;
        label.textContent = `${current} / ${pdf.numPages} 页`;
        status.hidden = true;
        prev.disabled = current <= 1; next.disabled = current >= pdf.numPages;
      } catch (error) {
        if (error.name !== "RenderingCancelledException") {
          status.textContent = "这一页暂时无法预览，可使用上方链接打开完整 PDF。";
          prev.disabled = current <= 1; next.disabled = current >= pdf.numPages;
        }
      }
    }
    prev.addEventListener("click", () => { if (current > 1) { current--; render(); } });
    next.addEventListener("click", () => { if (current < pdf.numPages) { current++; render(); } });
    let lastWidth = host.clientWidth;
    new ResizeObserver(() => {
      if (host.clientWidth === lastWidth) return;
      lastWidth = host.clientWidth;
      clearTimeout(resizeTimer); resizeTimer = setTimeout(render, 120);
    }).observe(host);
    await render();
  } catch (_) {
    status.textContent = "暂时无法加载预览。请使用上方链接打开或下载 PDF 原文件。";
  }
}

const observer = new IntersectionObserver(entries => {
  entries.filter(entry => entry.isIntersecting).forEach(entry => {
    observer.unobserve(entry.target); preview(entry.target);
  });
}, {rootMargin: "400px"});
document.querySelectorAll("[data-pdf-src]").forEach(node => observer.observe(node));
