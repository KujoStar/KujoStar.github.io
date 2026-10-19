/* Shared by the browser and Node's built-in test runner. No dependencies. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.NagisaSearch = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";
  const normalize = value => String(value || "").normalize("NFKC").toLocaleLowerCase().replace(/\s+/g, " ").trim();
  const prepared = new WeakMap();
  function fields(item) {
    if (!prepared.has(item)) prepared.set(item, {
      title: normalize(item.title),
      tags: normalize((item.tags || []).join(" ")),
      category: normalize(item.category + " " + item.subcategory),
      text: normalize((item.description || "") + " " + (item.text || ""))
    });
    return prepared.get(item);
  }
  function search(items, query) {
    const tokens = normalize(query).split(" ").filter(Boolean);
    if (!tokens.length) return [];
    return items.map(item => {
      const f = fields(item);
      let score = 0;
      for (const token of tokens) {
        if (f.title.includes(token)) score += 12;
        else if (f.tags.includes(token)) score += 8;
        else if (f.category.includes(token)) score += 5;
        else if (f.text.includes(token)) score += 1;
        else return null;
      }
      return {item, score};
    }).filter(Boolean).sort((a,b) => b.score - a.score || b.item.date.localeCompare(a.item.date) || a.item.id.localeCompare(b.item.id)).map(hit => hit.item);
  }
  function snippet(item, query, length = 145) {
    const text = (item.text || item.description || "").replace(/\s+/g, " ");
    const token = normalize(query).split(" ").find(Boolean) || "";
    const at = normalize(text).indexOf(token);
    const start = Math.max(0, at - 32);
    return (start ? "…" : "") + text.slice(start, start + length) + (start + length < text.length ? "…" : "");
  }
  return {normalize, search, snippet};
});
