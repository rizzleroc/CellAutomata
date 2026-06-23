/* web9 — cinematic origin-of-life interludes (#origin).
   Plays the two vertical clips only while they're on screen, and keeps the
   whole section hidden until at least one clip actually loads — so the page
   degrades cleanly while the clips are still being rendered.              */
(function () {
  "use strict";
  var section = document.getElementById("origin");
  if (!section) return;
  var vids = section.querySelectorAll(".cinema-clip video");
  if (!vids.length) return;

  var shown = false;
  function reveal() { if (!shown) { shown = true; section.style.display = ""; } }

  for (var i = 0; i < vids.length; i++) {
    (function (v) {
      var fig = v.closest(".cinema-clip");
      v.addEventListener("loadedmetadata", reveal, { once: true });
      v.addEventListener("error", function () { if (fig) fig.style.display = "none"; }, { once: true });
    })(vids[i]);
  }

  // play only what's in view; pause the rest to spare cycles
  function play(v) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      for (var j = 0; j < entries.length; j++) {
        if (entries[j].isIntersecting) play(entries[j].target);
        else entries[j].target.pause();
      }
    }, { threshold: 0.25 });
    for (var k = 0; k < vids.length; k++) io.observe(vids[k]);
  } else {
    for (var m = 0; m < vids.length; m++) play(vids[m]);
  }
})();
