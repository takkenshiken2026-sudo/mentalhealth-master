// Google Analytics 4 — window.__GA4_MEASUREMENT_ID__ で上書き可（未設定・空なら下記の既定ID）
// 測定IDの正: tools/html_footer.GA4_MEASUREMENT_ID と揃えること
(function () {
  var DEFAULT_MID = "G-KRCW0FBHM8";
  var raw = "";
  try {
    if (typeof window !== "undefined" && window.__GA4_MEASUREMENT_ID__ != null) {
      raw = String(window.__GA4_MEASUREMENT_ID__).trim();
    }
    if (!raw && typeof window !== "undefined" && window.SITE_CONFIG && window.SITE_CONFIG.ga4MeasurementId != null) {
      raw = String(window.SITE_CONFIG.ga4MeasurementId).trim();
    }
  } catch (_e) {}
  if (!raw) raw = DEFAULT_MID;
  var MID = /^G-[A-Za-z0-9]+$/.test(raw) ? raw : "";
  if (!MID) return;

  /**
   * SPA 等で URL・title が変わったあとに呼ぶ。index.html の gotoPage / popstate から利用。
   * 引数省略時は現在の location + document.title。
   */
  function ga4PageView(pagePath, pageTitle) {
    if (typeof window.gtag !== "function") return;
    var path = pagePath != null && String(pagePath) ? String(pagePath) : "";
    if (!path && typeof location !== "undefined") {
      path = location.pathname + location.search + location.hash;
    }
    var title = pageTitle != null ? String(pageTitle) : typeof document !== "undefined" ? document.title : "";
    try {
      var o = { page_path: path, page_title: title };
      if (typeof location !== "undefined" && location.href) {
        o.page_location = location.href;
      }
      window.gtag("config", MID, o);
    } catch (_e) {}
  }
  window.ga4PageView = ga4PageView;

  if (window.__GA4_SNIPPET_INIT__ === MID) return;
  window.__GA4_SNIPPET_INIT__ = MID;

  try {
    if (document.querySelector('script[src*="googletagmanager.com/gtag/js"][data-ga4-mid="' + MID + '"]')) {
      ga4PageView();
      return;
    }
  } catch (_e) {}

  window.dataLayer = window.dataLayer || [];
  function gtag() {
    window.dataLayer.push(arguments);
  }
  window.gtag = gtag;
  gtag("js", new Date());

  var s = document.createElement("script");
  s.async = true;
  s.setAttribute("data-ga4-mid", MID);
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(MID);
  document.head.appendChild(s);

  try {
    var cfg0 = {};
    if (typeof location !== "undefined" && location.href) {
      cfg0.page_location = location.href;
      cfg0.page_path = location.pathname + location.search + location.hash;
    }
    if (typeof document !== "undefined" && document.title) {
      cfg0.page_title = document.title;
    }
    gtag("config", MID, cfg0);
  } catch (_e2) {}
})();

// Microsoft Clarity — window.__CLARITY_PROJECT_ID__ / SITE_CONFIG.clarityProjectId で上書き可（未設定・空なら下記の既定ID）
(function () {
  var DEFAULT_PID = "zgaxqf7chk";
  var raw = "";
  try {
    if (typeof window !== "undefined" && window.__CLARITY_PROJECT_ID__ != null) {
      raw = String(window.__CLARITY_PROJECT_ID__).trim();
    }
    if (!raw && typeof window !== "undefined" && window.SITE_CONFIG && window.SITE_CONFIG.clarityProjectId != null) {
      raw = String(window.SITE_CONFIG.clarityProjectId).trim();
    }
  } catch (_e) {}
  if (!raw) raw = DEFAULT_PID;
  var PID = /^[A-Za-z0-9]+$/.test(raw) ? raw : "";
  if (!PID) return;

  // 二重初期化防止（SPA 再評価・複数読み込み対策）
  if (typeof window !== "undefined" && window.__CLARITY_INIT__ === PID) return;
  try {
    if (document.querySelector('script[src*="clarity.ms/tag/"][data-clarity-pid="' + PID + '"]')) {
      window.__CLARITY_INIT__ = PID;
      return;
    }
  } catch (_e) {}
  window.__CLARITY_INIT__ = PID;

  (function (c, l, a, r, i) {
    c[a] =
      c[a] ||
      function () {
        (c[a].q = c[a].q || []).push(arguments);
      };
    var t = l.createElement(r);
    t.async = 1;
    t.src = "https://www.clarity.ms/tag/" + i;
    t.setAttribute("data-clarity-pid", i);
    var y = l.getElementsByTagName(r)[0];
    y.parentNode.insertBefore(t, y);
  })(window, document, "clarity", "script", PID);
})();

// 有料教材（note）への導線クリックと、印刷の利用を計測（静的ページ共通・2026-11）。
// GA4 イベント: promo_click（promo_slot=static_<ページ種別>, promo_variant=mock|problem_book|other）、
//               print_click（「印刷する」ボタン）、print_open（印刷ダイアログを開いた＝Ctrl+P を含む）。
// トップ（SPA）の案内枠は onclick の trackPromoClick で計測済みのため二重に数えない。
(function () {
  if (typeof document === "undefined" || typeof window === "undefined") return;
  function send(name, params) {
    try {
      if (typeof window.gtag === "function") window.gtag("event", name, params);
    } catch (_e) {}
  }
  function slot() {
    var p = location.pathname || "";
    if (/\/q\/print\/field-/.test(p)) return "print_field";
    if (/\/q\/print\//.test(p)) return "print_hub";
    if (/\/q\/(index\.html)?$/.test(p)) return "q_index";
    if (/\/q\//.test(p)) return "q_question";
    if (/\/articles\//.test(p)) return "articles";
    if (/\/kaitou-sokuhou\//.test(p)) return "sokuhou";
    return "other";
  }
  document.addEventListener(
    "click",
    function (ev) {
      var t = ev.target;
      if (!t || !t.closest) return;
      var a = t.closest('a[href*="note.com/"]');
      if (a && !/trackPromo/.test(a.getAttribute("onclick") || "")) {
        var card = a.closest("[data-pick-kind]");
        var kind = card ? String(card.getAttribute("data-pick-kind") || "").replace("-", "_") : "";
        if (!kind) {
          var box = a.closest("article, li, p") || a;
          var text = (box.textContent || "") + " " + (a.textContent || "");
          kind = /模試/.test(text) ? "mock" : /問題集/.test(text) ? "problem_book" : "other";
        }
        send("promo_click", { promo_slot: "static_" + slot(), promo_variant: kind, link_url: a.href });
      }
      var b = t.closest("button.print-btn");
      if (b) send("print_click", { page_path: location.pathname, print_slot: slot() });
    },
    true
  );
  window.addEventListener("beforeprint", function () {
    send("print_open", { page_path: location.pathname, print_slot: slot() });
  });
})();
