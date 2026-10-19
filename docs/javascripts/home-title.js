(function () {
  "use strict";
  const heading = document.querySelector("[data-home-quotes]");
  if (!heading) return;

  const quotes = JSON.parse(heading.dataset.homeQuotes);
  const quote = quotes[Math.floor(Math.random() * quotes.length)];
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");
  const segmenter = typeof Intl.Segmenter === "function" ? new Intl.Segmenter(quote.lang, {granularity: "grapheme"}) : null;
  const letters = [];
  const fragment = document.createDocumentFragment();
  quote.lines.forEach((text, index) => {
    const line = document.createElement("span");
    line.className = "quote-line" + (index === quote.lines.length - 1 ? " quote-ending" : "");
    line.setAttribute("aria-hidden", "true");
    const characters = segmenter ? Array.from(segmenter.segment(text), item => item.segment) : Array.from(text);
    characters.forEach(character => {
      const letter = document.createElement("span");
      letter.className = "quote-letter";
      letter.textContent = character;
      line.append(letter);
      letters.push(letter);
    });
    fragment.append(line);
  });
  heading.lang = quote.lang;
  heading.setAttribute("aria-label", quote.lines.join(" "));
  heading.replaceChildren(fragment);
  if (reducedMotion.matches) return;

  // Keep the full text in the layout so wrapping and the search bar stay still.
  heading.classList.add("is-typing");
  let position = 0, timer;
  const delay = Math.min(42, 2800 / letters.length);
  function finish() {
    clearTimeout(timer);
    heading.classList.remove("is-typing");
    letters.forEach(letter => letter.classList.remove("is-cursor"));
    reducedMotion.removeEventListener("change", onMotionChange);
    document.removeEventListener("visibilitychange", onVisibilityChange);
    window.removeEventListener("pagehide", finish);
  }
  function typeNext() {
    if (position) letters[position - 1].classList.remove("is-cursor");
    const letter = letters[position++];
    letter.classList.add("is-typed", "is-cursor");
    const pause = /[,，;；:：.!?。！？]/u.test(letter.textContent) ? 150 : 0;
    timer = setTimeout(position < letters.length ? typeNext : finish, delay * (0.75 + Math.random() * 0.5) + pause);
  }
  function onMotionChange(event) { if (event.matches) finish(); }
  function onVisibilityChange() { if (document.hidden) finish(); }
  reducedMotion.addEventListener("change", onMotionChange);
  document.addEventListener("visibilitychange", onVisibilityChange);
  window.addEventListener("pagehide", finish);
  timer = setTimeout(typeNext, 180);
})();
