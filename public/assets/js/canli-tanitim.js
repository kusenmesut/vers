/* =====================================================================
   CANLI TANITIM — eDenetimPRO program demo alanı
   index.html içindeki #canli-tanitim iskeletini assets/data/canli_tanitim.json ile doldurur.
   İçerik admin panelinden (/canli-tanitim) yönetilir.
   ===================================================================== */
(function () {
  "use strict";
  var root = document.getElementById("canli-tanitim");
  if (!root) return;
  var DATA_URL = root.getAttribute("data-src") || "assets/data/canli_tanitim.json";

  var el = function (sel) { return root.querySelector(sel); };
  var list = el(".ct-dir-list"), count = el(".ct-dir-count"), view = el(".ct-view"), img = el(".ct-view img"),
      empty = el(".ct-empty"), prev = el(".ct-arrow.prev"), next = el(".ct-arrow.next"), badge = el(".ct-badge"),
      caption = el(".ct-caption"), thumbs = el(".ct-thumbs"), meta = el(".ct-meta"), title = el(".ct-title"),
      slogan = el(".ct-slogan"), desc = el(".ct-desc"), bullets = el(".ct-bullets");
  var items = [], cur = -1, pic = 0, zoom = null;

  function pad(n) { return (n < 10 ? "0" : "") + n; }
  // Menüdeki BÜYÜK HARFLİ başlıkları okunur yapar; kısaltmalar ve .xml gibi parçalar korunur.
  var KEEP = { KDV: 1, YMM: 1, GIB: 1, "GİB": 1, MR: 1, XML: 1, ZIP: 1, XLS: 1, VKN: 1, PDF: 1 };
  var SMALL = { VE: "ve", "İLE": "ile", VEYA: "veya" };
  function nice(s) {
    return String(s || "").split(/(\s+|[()\/\-.,])/).map(function (w, i) {
      if (!w || !/[A-Za-zÇĞİÖŞÜçğıöşü]/.test(w)) return w;
      if (w !== w.toLocaleUpperCase("tr-TR")) return w;               // zaten karışık / küçük
      if (KEEP[w]) return w;
      if (SMALL[w] && i > 0) return SMALL[w];
      var low = w.toLocaleLowerCase("tr-TR");
      return low.charAt(0).toLocaleUpperCase("tr-TR") + low.slice(1);
    }).join("");
  }
  function text(node, value) { node.textContent = value || ""; }

  // ---- Sol menü: programdaki gibi açılır kapanır ana menüler ------------
  var GROUPS = [], openGid = null, search = root.querySelector(".ct-search input"), home = root.querySelector(".ct-home");
  var FALLBACK_ICON = "▣";

  function fold(s) { return String(s || "").toLocaleLowerCase("tr-TR"); }
  function markText(node, label, q) {
    var i = q ? fold(label).indexOf(q) : -1;
    if (i < 0) { node.textContent = label; return; }
    node.appendChild(document.createTextNode(label.slice(0, i)));
    var m = document.createElement("mark"); m.textContent = label.slice(i, i + q.length); node.appendChild(m);
    node.appendChild(document.createTextNode(label.slice(i + q.length)));
  }

  function buildList(groups) {
    GROUPS = groups; items = [];
    groups.forEach(function (g) { g.items.forEach(function (it) { items.push({ g: g, it: it }); }); });
  }

  function renderMenu() {
    var q = fold(search && search.value).trim(), curG = items[cur] ? items[cur].g.id : null, shown = 0;
    list.innerHTML = "";
    GROUPS.forEach(function (g) {
      var hits = g.items.filter(function (it) { return !q || fold(it.title).indexOf(q) >= 0 || fold(g.title).indexOf(q) >= 0; });
      if (!hits.length) return;
      var isOpen = q ? true : openGid === g.id;
      var head = document.createElement("button");
      head.type = "button";
      head.className = "ct-grp" + (g.id === curG ? " cur" : "");
      head.setAttribute("aria-expanded", isOpen ? "true" : "false");
      head.innerHTML = '<span class="ct-gi" aria-hidden="true"></span><span class="ct-gt"></span><span class="ct-ga" aria-hidden="true">' + (isOpen ? "▼" : "▶") + "</span>";
      head.firstChild.textContent = g.icon || FALLBACK_ICON;
      markText(head.children[1], g.title, q && fold(g.title).indexOf(q) >= 0 ? q : "");
      head.addEventListener("click", function () { openGid = openGid === g.id ? null : g.id; renderMenu(); });
      list.appendChild(head);
      if (!isOpen) return;
      var sub = document.createElement("div");
      sub.className = "ct-sub";
      hits.forEach(function (it) {
        var idx = -1;
        items.forEach(function (x, i) { if (x.it === it) idx = i; });
        var b = document.createElement("button");
        b.type = "button";
        b.className = "ct-item" + ((it.images || []).length ? "" : " empty") + (idx === cur ? " on" : "");
        b.setAttribute("data-idx", idx);
        markText(b, it.title, q);
        b.addEventListener("click", function () { select(idx, true); });
        sub.appendChild(b);
        shown++;
      });
      list.appendChild(sub);
    });
    if (!list.children.length) {
      var none = document.createElement("div"); none.className = "ct-nores"; none.textContent = "Eşleşen menü yok."; list.appendChild(none);
    }
  }

  if (search) search.addEventListener("input", renderMenu);
  if (home) home.addEventListener("click", function () {
    if (search) search.value = "";
    var first = 0;
    for (var i = 0; i < items.length; i++) { if ((items[i].it.images || []).length) { first = i; break; } }
    select(first, true);
    list.scrollTop = 0;
  });

  function showPicture() {
    var it = items[cur].it, pics = it.images || [], n = pics.length;
    tour = -1;
    prev.hidden = next.hidden = n < 2;
    badge.innerHTML = n ? pad(pic + 1) + ' <small>/ ' + pad(n) + "</small>" : "";
    badge.style.display = n ? "" : "none";
    if (!n) {
      img.removeAttribute("src"); img.classList.remove("ready"); img.style.display = "none";
      empty.style.display = ""; text(caption, ""); renderTips(); return;
    }
    empty.style.display = "none"; img.style.display = "";
    var p = pics[pic];
    img.classList.remove("ready");
    tipLayer.innerHTML = "";
    img.onload = function () { img.classList.add("ready"); renderTips(); };
    img.src = p.src;
    img.alt = nice(it.title) + (p.caption ? " — " + p.caption : "");
    if (img.complete && img.naturalWidth) { img.classList.add("ready"); renderTips(); } else { tipBtn.hidden = true; }
    text(caption, p.caption);
    [].forEach.call(thumbs.children, function (t, i) { t.classList.toggle("on", i === pic); });
    var on = thumbs.children[pic];
    if (on && on.scrollIntoView) on.scrollIntoView({ block: "nearest", inline: "nearest" });
    if (pics[pic + 1]) { var pre = new Image(); pre.src = pics[pic + 1].src; }   // sonrakini önden yükle
  }

  // ---- İpucu turu: resim üzerindeki açıklama kutuları ------------------
  var tipLayer = document.createElement("div"), tipBtn = document.createElement("button"), tour = -1;
  tipLayer.className = "ct-tips"; view.appendChild(tipLayer);
  tipBtn.type = "button"; tipBtn.className = "ct-tipbtn"; tipBtn.hidden = true; view.appendChild(tipBtn);
  tipBtn.addEventListener("click", function () { startTour(0); });

  function curTips() {
    var x = items[cur], p = x && (x.it.images || [])[pic];
    return (p && p.ipuclari) || [];
  }
  function imgRect() {
    var W = view.clientWidth, H = view.clientHeight, nw = img.naturalWidth, nh = img.naturalHeight;
    if (!nw || !nh || img.style.display === "none") return null;
    var s = Math.min(W / nw, H / nh), w = nw * s, h = nh * s;
    return { l: (W - w) / 2, t: (H - h) / 2, w: w, h: h, W: W, H: H };
  }
  function richText(s) {
    var div = document.createElement("div"); div.textContent = s || "";
    return div.innerHTML.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>");
  }
  function renderTips() {
    var tips = curTips();
    tipBtn.hidden = !tips.length;
    tipBtn.textContent = "💡 İpuçları (" + tips.length + ")";
    layoutTips();
  }
  function layoutTips() {
    var r = imgRect(), tips = curTips();
    tipLayer.innerHTML = "";
    view.classList.toggle("touring", tour >= 0);
    if (!r || !tips.length) { tipLayer.style.display = "none"; return; }
    tipLayer.style.display = "";
    tipLayer.style.left = r.l + "px"; tipLayer.style.top = r.t + "px";
    tipLayer.style.width = r.w + "px"; tipLayer.style.height = r.h + "px";
    var px = function (t) { return { x: t.x / 100 * r.w, y: t.y / 100 * r.h, w: t.w / 100 * r.w, h: t.h / 100 * r.h }; };
    if (tour < 0) {
      tips.forEach(function (t, i) {
        var a = px(t), d = document.createElement("button");
        d.type = "button"; d.className = "ct-dot"; d.textContent = i + 1;
        d.title = t.baslik || ("İpucu " + (i + 1));
        d.setAttribute("aria-label", (i + 1) + ". ipucu: " + (t.baslik || ""));
        d.style.left = (a.x + a.w / 2) + "px"; d.style.top = (a.y + a.h / 2) + "px";
        d.addEventListener("click", function (e) { e.stopPropagation(); startTour(i); });
        tipLayer.appendChild(d);
      });
      return;
    }
    var t = tips[tour], a = px(t), pad = 5;
    var spot = document.createElement("div");
    spot.className = "ct-spot";
    spot.style.left = (a.x - pad) + "px"; spot.style.top = (a.y - pad) + "px";
    spot.style.width = (a.w + pad * 2) + "px"; spot.style.height = (a.h + pad * 2) + "px";
    tipLayer.appendChild(spot);
    var box = document.createElement("div");
    box.className = "ct-tip"; box.setAttribute("role", "dialog");
    box.innerHTML = '<button type="button" class="ct-tipx" aria-label="Kapat">×</button><h5></h5><p></p>' +
      '<div class="ct-tipnav"><span></span>' + (tour > 0 ? '<button type="button" class="ct-tipprev">← Geri</button>' : "") +
      '<button type="button" class="ct-tipnext">' + (tour < tips.length - 1 ? "İleri →" : "Bitti ✓") + "</button></div>";
    box.querySelector("h5").appendChild(document.createTextNode(t.baslik || ("İpucu " + (tour + 1))));
    box.querySelector("p").innerHTML = richText(t.metin);
    box.querySelector(".ct-tipnav span").textContent = (tour + 1) + " / " + tips.length;
    box.querySelector(".ct-tipx").addEventListener("click", endTour);
    box.querySelector(".ct-tipnext").addEventListener("click", function () { tour < tips.length - 1 ? goTip(1) : endTour(); });
    var pb = box.querySelector(".ct-tipprev"); if (pb) pb.addEventListener("click", function () { goTip(-1); });
    tipLayer.appendChild(box);
    // Kutuyu alanın boş tarafına yerleştir (görünüm koordinatı -> katman koordinatı)
    var bw = box.offsetWidth, bh = box.offsetHeight, gap = 18, vx = r.l + a.x, vy = r.t + a.y, side, bx, by;
    if (vx + a.w + gap + bw <= r.W - 8) { side = "right"; bx = vx + a.w + gap; by = vy; }
    else if (vx - gap - bw >= 8) { side = "left"; bx = vx - gap - bw; by = vy; }
    else if (vy + a.h + gap + bh <= r.H - 8) { side = "below"; bx = vx; by = vy + a.h + gap; }
    else { side = "above"; bx = vx; by = vy - gap - bh; }
    bx = Math.max(8, Math.min(bx, r.W - bw - 8)); by = Math.max(8, Math.min(by, r.H - bh - 8));
    box.className = "ct-tip " + side;
    box.style.left = (bx - r.l) + "px"; box.style.top = (by - r.t) + "px";
    var nx = box.querySelector(".ct-tipnext"); if (nx && nx.focus) nx.focus({ preventScroll: true });
  }
  function startTour(i) { if (!curTips().length) return; tour = i; layoutTips(); }
  function goTip(d) { var n = curTips().length; tour = Math.max(0, Math.min(n - 1, tour + d)); layoutTips(); }
  function endTour() { if (tour < 0) return; tour = -1; layoutTips(); try { view.focus({ preventScroll: true }); } catch (e) {} }
  view.addEventListener("keydown", function (e) {
    if (tour < 0) return;
    if (e.key === "ArrowRight") { goTip(1); } else if (e.key === "ArrowLeft") { goTip(-1); } else if (e.key === "Escape") { endTour(); } else return;
    e.preventDefault(); e.stopImmediatePropagation();
  }, true);
  img.addEventListener("click", function (e) { if (tour >= 0) { e.stopImmediatePropagation(); endTour(); } }, true);
  var resizeJob = null;
  window.addEventListener("resize", function () { clearTimeout(resizeJob); resizeJob = setTimeout(layoutTips, 120); });

  function select(idx, fromUser) {
    if (idx < 0 || idx >= items.length) return;
    cur = idx; pic = 0;
    var x = items[idx], it = x.it;
    openGid = x.g.id;
    renderMenu();
    var active = list.querySelector(".ct-item.on");
    if (active) {
      var top = active.offsetTop - list.offsetTop, bottom = top + active.offsetHeight;
      if (top < list.scrollTop || bottom > list.scrollTop + list.clientHeight) list.scrollTop = Math.max(0, top - 80);
    }
    if (count) text(count, pad(idx + 1) + " / " + pad(items.length));
    meta.innerHTML = "<span></span><span class=\"ct-mod\">MODÜL " + pad(idx + 1) + "</span>";
    meta.firstChild.textContent = x.g.title;
    text(title, nice(it.title)); text(slogan, it.slogan); text(desc, it.aciklama);
    bullets.innerHTML = "";
    (it.maddeler || []).forEach(function (m) { var li = document.createElement("li"); li.textContent = m; bullets.appendChild(li); });
    thumbs.innerHTML = "";
    var pics = it.images || [];
    if (pics.length > 1) pics.forEach(function (p, i) {
      var t = document.createElement("button");
      t.type = "button"; t.className = "ct-thumb";
      t.setAttribute("aria-label", (i + 1) + ". resim" + (p.caption ? ": " + p.caption : ""));
      t.innerHTML = '<img loading="lazy" alt="">';
      t.firstChild.src = p.src;
      t.addEventListener("click", function () { pic = i; showPicture(); });
      thumbs.appendChild(t);
    });
    showPicture();
    if (fromUser === true && window.history && history.replaceState) history.replaceState(null, "", "#modul-" + it.slug);
  }

  function step(dir) {
    var n = (items[cur] && items[cur].it.images || []).length;
    if (n < 2) return;
    pic = (pic + dir + n) % n;
    showPicture();
  }

  prev.addEventListener("click", function () { step(-1); });
  next.addEventListener("click", function () { step(1); });
  view.addEventListener("keydown", function (e) {
    if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    if (e.key === "ArrowRight") { e.preventDefault(); step(1); }
  });
  list.addEventListener("keydown", function (e) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    if (!e.target.classList.contains("ct-item")) return;   // grup başlıklarında tarayıcı davranışı kalsın
    e.preventDefault();
    var visible = [].map.call(list.querySelectorAll(".ct-item"), function (b) { return +b.getAttribute("data-idx"); });
    var pos = visible.indexOf(cur) + (e.key === "ArrowDown" ? 1 : -1);
    if (pos < 0 || pos >= visible.length) return;
    select(visible[pos], true);
    var b = list.querySelector(".ct-item.on"); if (b) b.focus();
  });
  var sx = null;
  view.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; }, { passive: true });
  view.addEventListener("touchend", function (e) {
    if (sx === null) return;
    var dx = e.changedTouches[0].clientX - sx; sx = null;
    if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1);
  });
  img.addEventListener("click", function () {
    if (!img.src) return;
    if (!zoom) {
      zoom = document.createElement("div"); zoom.className = "ct-zoom"; zoom.innerHTML = "<img alt=\"\">";
      zoom.addEventListener("click", function () { zoom.classList.remove("on"); });
      document.addEventListener("keydown", function (e) { if (e.key === "Escape") zoom.classList.remove("on"); });
      document.body.appendChild(zoom);
    }
    zoom.firstChild.src = img.src; zoom.classList.add("on");
  });

  function start(data) {
    var meta0 = data.meta || {};
    if (meta0.baslik) { var h = root.querySelector("[data-ct-baslik]"); if (h) h.textContent = meta0.baslik; }
    if (meta0.alt_baslik) { var a = root.querySelector("[data-ct-alt]"); if (a) a.textContent = meta0.alt_baslik; }
    var groups = (data.groups || []).filter(function (g) { return !g.hidden; }).map(function (g) {
      return { id: g.id, title: g.title, icon: g.icon, items: (g.items || []).filter(function (i) { return !i.hidden; }) };
    }).filter(function (g) { return g.items.length; });
    buildList(groups);
    if (!items.length) { root.style.display = "none"; return; }
    var wanted = (location.hash.match(/^#modul-(.+)$/) || [])[1], start = -1;
    if (wanted) items.forEach(function (x, i) { if (x.it.slug === decodeURIComponent(wanted)) start = i; });
    if (start < 0) items.forEach(function (x, i) { if (start < 0 && (x.it.images || []).length) start = i; });
    select(start < 0 ? 0 : start, "init");
    if (wanted && start >= 0) {
      // Site açılışta preloader ve yumuşak kaydırma kullanıyor; yükleme bitince anında kaydır.
      var jump = function () {
        setTimeout(function () {
          var y = root.getBoundingClientRect().top + window.pageYOffset - 70;
          try { window.scrollTo({ top: y, behavior: "instant" }); } catch (e) { window.scrollTo(0, y); }
        }, 450);
      };
      if (document.readyState === "complete") jump(); else window.addEventListener("load", jump);
    }
  }

  fetch(DATA_URL + "?v=" + Date.now(), { cache: "no-store" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(start)
    .catch(function (err) {
      console.warn("[Canlı tanıtım] Veri yüklenemedi:", err);
      root.style.display = "none";
    });
})();
