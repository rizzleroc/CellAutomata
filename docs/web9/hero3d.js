/* hero3d.js — the real 3D rendered mitosis in the page.
   Loads the marching-cubes cleavage sequence (assets/cleavage.bin) and plays it
   as a WebGL mesh flipbook with a translucent bioluminescent membrane. Exposes
   window.protocellHero.load(url) so the render bridge can hot-swap in a freshly
   simulated cell. Falls back to the 2D canvas hero if WebGL/data is missing. */
(function () {
  "use strict";
  var canvas = document.getElementById("hero3d");
  if (!canvas || typeof THREE === "undefined") return;

  var renderer;
  try { renderer = new THREE.WebGLRenderer({ canvas: canvas, antialias: true, alpha: true }); }
  catch (e) { return; }

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(34, 1, 0.1, 5000);
  var baseDist = 60;
  camera.position.set(0, 0, baseDist); camera.lookAt(0, 0, 0);

  var VERT =
    "varying vec3 vN; varying vec3 vView; varying vec3 vP;" +
    "void main(){ vec4 wp = modelMatrix * vec4(position,1.0);" +
    " vN = normalize(mat3(modelMatrix) * normal); vView = normalize(cameraPosition - wp.xyz);" +
    " vP = position; gl_Position = projectionMatrix * viewMatrix * wp; }";

  var mat = new THREE.ShaderMaterial({
    uniforms: { uCore: { value: new THREE.Color(0.06, 0.30, 0.95) }, uRim: { value: new THREE.Color(0.35, 0.95, 1.0) } },
    vertexShader: VERT,
    fragmentShader:
      "uniform vec3 uCore; uniform vec3 uRim; varying vec3 vN; varying vec3 vView; varying vec3 vP;" +
      "float hash(vec3 p){ return fract(sin(dot(floor(p), vec3(12.9898,78.233,37.719)))*43758.5453); }" +
      "void main(){ float ndv = clamp(dot(normalize(vN), normalize(vView)),0.0,1.0);" +
      " float fres = pow(1.0-ndv,2.0); float gran = 0.85 + 0.30*hash(vP*6.0);" +
      " vec3 body = uCore*(0.08+0.16*ndv)*gran; vec3 rim = uRim*fres*3.4; float hot = pow(fres,2.6);" +
      " vec3 col = body + rim + uRim*hot*1.4; float a = clamp(fres*1.25+0.07,0.0,1.0);" +
      " gl_FragColor = vec4(col, a); }",
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide
  });
  var glow = new THREE.ShaderMaterial({
    uniforms: { uRim: { value: new THREE.Color(0.30, 0.85, 1.0) } },
    vertexShader: VERT,
    fragmentShader:
      "uniform vec3 uRim; varying vec3 vN; varying vec3 vView; varying vec3 vP;" +
      "void main(){ float ndv = clamp(dot(normalize(vN), normalize(vView)),0.0,1.0);" +
      " float f = pow(1.0-ndv,1.3); gl_FragColor = vec4(uRim*f*1.3, f*0.45); }",
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.BackSide
  });

  var group = new THREE.Group();
  var mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
  var halo = new THREE.Mesh(new THREE.BufferGeometry(), glow);
  halo.scale.setScalar(1.07);
  group.add(halo); group.add(mesh); scene.add(group);

  var geos = [];
  function parseBuffer(buf) {
    var dv = new DataView(buf), off = 0;
    if (dv.getUint32(off, true) !== 0x4D435631) return null; off += 4;
    var frameCount = dv.getUint32(off, true); off += 4;
    var out = [], maxExtent = 1;
    for (var f = 0; f < frameCount; f++) {
      var vc = dv.getUint32(off, true); off += 4;
      var tc = dv.getUint32(off, true); off += 4;
      var pos = new Float32Array(buf, off, vc * 3); off += vc * 3 * 4;
      var nrm = new Float32Array(buf, off, vc * 3); off += vc * 3 * 4;
      var idx = new Uint32Array(buf, off, tc * 3); off += tc * 3 * 4;
      var g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
      g.setAttribute("normal", new THREE.BufferAttribute(nrm, 3));
      g.setIndex(new THREE.BufferAttribute(idx, 1));
      g.computeBoundingSphere();
      if (g.boundingSphere) maxExtent = Math.max(maxExtent, g.boundingSphere.radius);
      out.push(g);
    }
    return { geos: out, maxExtent: maxExtent };
  }
  function setGeometry(parsed) {
    var i;
    for (i = 0; i < geos.length; i++) geos[i].dispose();
    geos = parsed.geos;
    baseDist = parsed.maxExtent * 3.0;
    fi = 0; dir = 1;
    mesh.geometry = geos[0]; halo.geometry = geos[0];
  }

  function resize() {
    var w = canvas.clientWidth || 540, h = canvas.clientHeight || 960;
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    renderer.setSize(w, h, false);
    camera.aspect = w / h; camera.updateProjectionMatrix();
  }
  resize();
  window.addEventListener("resize", resize);

  var clock = new THREE.Clock();
  var fi = 0, dir = 1, acc = 0, started = false;
  var phaseEl = document.getElementById("hero-phase");
  function setPhase(t) { if (phaseEl) phaseEl.textContent = t < 0.30 ? "single cell" : t < 0.50 ? "elongating" : t < 0.62 ? "cleavage furrow" : "two daughters"; }
  function animate() {
    requestAnimationFrame(animate);
    if (!geos.length) return;
    var dt = Math.min(0.05, clock.getDelta());
    var st = window.heroState || { playing: true, rotate: true, scrub: 0, zoom: 1.6 };
    camera.position.z = baseDist / (st.zoom || 1.6);
    if (st.rotate) group.rotation.y += dt * 0.42;
    group.rotation.x = Math.sin(clock.elapsedTime * 0.13) * 0.10;
    if (st.playing) {
      acc += dt;
      if (acc > 0.075) { acc = 0; fi += dir; if (fi >= geos.length - 1) { fi = geos.length - 1; dir = -1; } else if (fi <= 0) { fi = 0; dir = 1; } }
      st.scrub = fi / (geos.length - 1);
    } else { fi = Math.round(st.scrub * (geos.length - 1)); }
    mesh.geometry = geos[fi]; halo.geometry = geos[fi];
    setPhase(fi / (geos.length - 1));
    renderer.render(scene, camera);
  }

  function takeOver() {
    var hero2d = document.getElementById("hero");
    if (hero2d) hero2d.style.display = "none";
    canvas.style.display = "block";
    window.__stop2D = true;
    if (!started) { started = true; animate(); }
  }
  function loadUrl(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error("bad"); return r.arrayBuffer(); })
      .then(function (buf) { var p = parseBuffer(buf); if (p) { setGeometry(p); takeOver(); } return !!p; });
  }

  // public: let the render bridge hot-swap a freshly simulated cell
  window.protocellHero = { load: loadUrl };

  loadUrl("assets/cleavage.bin").catch(function () { /* keep 2D hero */ });
})();
