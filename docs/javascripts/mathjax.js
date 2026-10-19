window.MathJax = {
  tex: {
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"]],
    processEscapes: true,
    tags: "ams",
    macros: {bm: ["\\boldsymbol{#1}", 1]}
  },
  options: {ignoreHtmlClass: ".*|", processHtmlClass: "arithmatex"},
  chtml: {matchFontHeight: false}
};
