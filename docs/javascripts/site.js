(function () {
  "use strict";
  document.documentElement.classList.add("js");
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const media = matchMedia("(prefers-color-scheme: dark)");
  const themeButton = $(".theme-toggle");

  function themeName() { return document.documentElement.dataset.theme === "slate" ? "dark_dimmed" : "light"; }
  function setTheme(value, persist = false) {
    document.documentElement.dataset.theme = value;
    document.documentElement.style.colorScheme = value === "slate" ? "dark" : "light";
    document.body.dataset.mdColorScheme = value;
    themeButton?.setAttribute("aria-label", value === "slate" ? "切换到浅色主题" : "切换到深色主题");
    if (persist) { try { localStorage.setItem("nagisa.theme", value); } catch (_) {} }
    $("iframe.giscus-frame")?.contentWindow?.postMessage({giscus: {setConfig: {theme: themeName()}}}, "https://giscus.app");
  }
  setTheme(document.documentElement.dataset.theme || "default");
  themeButton?.addEventListener("click", () => setTheme(document.documentElement.dataset.theme === "slate" ? "default" : "slate", true));
  media.addEventListener("change", event => {
    let saved; try { saved = localStorage.getItem("nagisa.theme"); } catch (_) {}
    if (!saved) setTheme(event.matches ? "slate" : "default");
  });

  // Native dialogs provide focus trapping and return focus to their opener.
  $$('[data-close-dialog]').forEach(button => button.addEventListener("click", () => button.closest("dialog").close()));
  $$("dialog").forEach(dialog => dialog.addEventListener("click", event => {
    if (event.target !== dialog) return;
    const r = dialog.getBoundingClientRect();
    if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close();
  }));

  function hashValue() {
    try { return decodeURIComponent(location.hash.slice(1)); } catch (_) { return ""; }
  }
  function selectShelf() {
    const shelves = $(".shelves");
    if (!shelves) return;
    const key = hashValue(), category = key.split("--")[0];
    const shelf = $$('[data-shelf]').find(s => s.id === category);
    $$('[data-shelf]').forEach(s => s.classList.toggle("is-selected", s === shelf));
    shelves.classList.toggle("has-selection", Boolean(shelf));
    $(".category-index")?.classList.toggle("is-hidden", Boolean(shelf));
    $(".page-heading")?.classList.toggle("is-hidden", Boolean(shelf));
    if (shelf) {
      const book = $$("details.book", shelf).find(b => b.id === key);
      if (book) book.open = true;
    }
  }
  function filterTags() {
    const results = $(".tag-results");
    if (!results) return;
    const tag = hashValue();
    let count = 0;
    $$(".article-row", results).forEach(row => {
      const tags = JSON.parse(row.dataset.tags || "[]");
      row.hidden = Boolean(tag && !tags.includes(tag));
      if (!row.hidden) count++;
    });
    $$(".tag-filter").forEach(a => a.setAttribute("aria-current", String((a.dataset.tag || "") === tag)));
    $(".filter-status").textContent = (tag ? `#${tag} · ` : "全部 · ") + `${count} 篇`;
    $(".tag-empty").hidden = count > 0;
  }
  selectShelf(); filterTags();
  const archiveOrder = $("#archive-order"), archiveList = $("#archive-list");
  if (archiveOrder && archiveList) {
    const newestFirst = Array.from(archiveList.children);
    function sortArchives() {
      const oldestFirst = archiveOrder.value === "oldest";
      archiveList.replaceChildren(...(oldestFirst ? newestFirst.slice().reverse() : newestFirst));
      $("#archive-status").textContent = `已按发布时间${oldestFirst ? "从旧到新" : "从新到旧"}排列，共 ${newestFirst.length} 篇文章`;
    }
    archiveOrder.closest("label").hidden = false;
    archiveOrder.addEventListener("change", sortArchives);
    addEventListener("pageshow", sortArchives);
    sortArchives();
  }
  addEventListener("hashchange", () => {
    selectShelf(); filterTags();
    if ($(".shelves")) window.scrollTo({top: 0, behavior: "instant"});
  });
  $$(".book-close").forEach(button => button.addEventListener("click", () => {
    const book = button.closest("details"); book.open = false; $("summary", book).focus();
  }));
  $$("details.book").forEach(book => book.addEventListener("toggle", () => {
    if (book.open) $$("details.book", book.closest(".shelf")).forEach(other => { if (other !== book) other.open = false; });
  }));

  const searchDialog = $("#search-dialog");
  const queryInput = $("#search-query");
  let catalogPromise, fullPromise, revision = 0, timer;
  async function getJSON(url, fresh = false) {
    const response = await fetch(url, {cache: fresh ? "reload" : "default"});
    if (!response.ok) throw new Error(`Search HTTP ${response.status}`);
    const data = await response.json();
    if (!data.version || !Array.isArray(data.items)) throw new Error("Invalid search data");
    return data;
  }
  function catalog() {
    if (!catalogPromise) catalogPromise = getJSON("/assets/catalog.json").catch(error => { catalogPromise = null; throw error; });
    return catalogPromise;
  }
  function fullIndex() {
    if (!fullPromise) fullPromise = (async () => {
      let [light, full] = await Promise.all([catalog(), getJSON("/assets/search.json")]);
      if (light.version !== full.version) {
        [light, full] = await Promise.all([getJSON("/assets/catalog.json", true), getJSON("/assets/search.json", true)]);
        if (light.version !== full.version) throw new Error("Index is being updated");
        catalogPromise = Promise.resolve(light);
      }
      return full;
    })().catch(error => { fullPromise = null; throw error; });
    return fullPromise;
  }
  function renderResults(items, query) {
    const list = $(".search-results"); list.replaceChildren();
    items.slice(0, 30).forEach(item => {
      const li = document.createElement("li"), link = document.createElement("a");
      link.href = item.url;
      const title = document.createElement("strong"); title.textContent = item.title;
      const meta = document.createElement("small"); meta.textContent = `${item.category} / ${item.subcategory} · ${item.date}`;
      const text = document.createElement("p"); text.textContent = window.NagisaSearch.snippet(item, query);
      link.append(title, meta, text); li.append(link); list.append(li);
    });
  }
  async function runSearch() {
    const version = ++revision, query = queryInput.value.trim(), status = $(".search-status");
    if (!query) { renderResults([], ""); status.textContent = ""; return; }
    status.textContent = "正在查找……";
    try {
      const light = await catalog();
      if (version !== revision) return;
      renderResults(window.NagisaSearch.search(light.items, query), query);
      const full = await fullIndex();
      if (version !== revision) return;
      const results = window.NagisaSearch.search(full.items, query);
      renderResults(results, query);
      status.textContent = results.length ? `共 ${results.length} 篇${results.length > 30 ? "，显示前 30 篇" : ""}` : "无搜索结果";
    } catch (_) {
      if (version === revision) status.textContent = "搜索加载失败，按 Enter 重试。";
    }
  }
  function openSearch(query = "") {
    if (!searchDialog) return;
    queryInput.value = query;
    if (!searchDialog.open) searchDialog.showModal();
    queryInput.focus();
    catalog().catch(() => {});
    runSearch();
  }
  $$('[data-open-search]').forEach(button => button.addEventListener("click", () => openSearch()));
  $("[data-home-search]")?.addEventListener("submit", event => { event.preventDefault(); openSearch($("#home-query").value); });
  $("#home-query")?.addEventListener("focus", () => catalog().catch(() => {}));
  queryInput?.addEventListener("input", () => { revision++; clearTimeout(timer); timer = setTimeout(runSearch, 180); });
  $("#search-form")?.addEventListener("submit", event => { event.preventDefault(); clearTimeout(timer); runSearch(); });
  searchDialog?.addEventListener("close", () => { revision++; clearTimeout(timer); });
  document.addEventListener("keydown", event => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); openSearch(); }
    if (event.key === "Escape" && !$("dialog[open]")) {
      const book = $("details.book[open]");
      if (book) { book.open = false; $("summary", book).focus(); }
    }
  });

  const headings = $$("#article-body h2[id],#article-body h3[id],#article-body h4[id],#article-body h5[id],#article-body h6[id]");
  $$("#article-body .highlight").forEach(block => {
    const code = $("pre code", block);
    if (!code) return;
    const button = document.createElement("button");
    button.type = "button"; button.className = "code-copy";
    button.textContent = "复制"; button.setAttribute("aria-label", "复制代码");
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = "已复制";
      } catch (_) {
        const selection = window.getSelection(), range = document.createRange();
        range.selectNodeContents(code); selection.removeAllRanges(); selection.addRange(range);
        button.textContent = "请按 Ctrl+C";
      }
      setTimeout(() => { button.textContent = "复制"; }, 1800);
    });
    block.append(button);
  });
  const tocButton = $("[data-open-toc]");
  if (headings.length && tocButton) {
    headings.forEach(heading => {
      const a = document.createElement("a");
      a.href = "#" + encodeURIComponent(heading.id);
      a.textContent = heading.textContent.replace(/¶$/, "");
      a.dataset.level = heading.tagName.slice(1);
      a.addEventListener("click", () => $("#toc-dialog").close());
      $(".mobile-toc").append(a);
    });
    tocButton.hidden = false;
    tocButton.addEventListener("click", () => $("#toc-dialog").showModal());
  }
  $$("#article-body img").forEach(img => {
    if (img.closest("a")) return;
    img.tabIndex = 0; img.setAttribute("role", "button");
    img.setAttribute("aria-label", "放大图片：" + (img.alt || "文章插图"));
    function openImage() {
      const dialog = $("#image-dialog"), enlarged = $("img", dialog);
      enlarged.src = img.currentSrc || img.src; enlarged.alt = img.alt;
      $("a", dialog).href = enlarged.src;
      dialog.showModal();
    }
    img.addEventListener("click", openImage);
    img.addEventListener("keydown", event => { if (["Enter", " "].includes(event.key)) { event.preventDefault(); openImage(); } });
  });
  const comments = $("[data-giscus-config]");
  if (comments) {
    const config = JSON.parse(comments.dataset.giscusConfig);
    const loadComments = () => {
      const script = document.createElement("script"); script.src = "https://giscus.app/client.js";
      script.async = true; script.crossOrigin = "anonymous";
      const attrs = {repo: config.repo, "repo-id": config.repo_id, category: config.category, "category-id": config.category_id, mapping: "specific", term: config.term, strict: "1", "reactions-enabled": "1", "emit-metadata": "0", "input-position": "top", theme: themeName(), lang: "zh-CN", loading: "lazy"};
      Object.entries(attrs).forEach(([key, value]) => script.setAttribute("data-" + key, value));
      comments.append(script);
    };
    const observer = new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) { observer.disconnect(); loadComments(); } }, {rootMargin: "300px"});
    observer.observe(comments);
  }
})();
