/* 解答速報：自己採点チェッカー（合格ライン判定＋結果画像のXシェア）
 * - 入力した得点は端末内でのみ処理（送信・保存なし）。
 * - 画像は <canvas> で生成。Xのweb intentは画像を自動添付できないため、
 *   「画像を保存」＋手動添付、またはスマホの Web Share API（画像付き共有）に対応。
 */
(function () {
  "use strict";

  var ACCENT = "#4a6b5c";
  var STATE = {
    pass: { label: "合格ラインに到達", color: "#1f7a4d", bg: "#e7f4ec" },
    border: { label: "ボーダー付近", color: "#9a6a00", bg: "#fbf1dc" },
    miss: { label: "合格ラインまであと少し", color: "#8a3d3d", bg: "#f7e9e9" }
  };

  function num(v) {
    var n = parseInt(String(v).replace(/[^0-9-]/g, ""), 10);
    return isNaN(n) ? null : n;
  }

  function judge(score, pass, max) {
    if (pass == null) return { key: "none" };
    if (score >= pass) return { key: "pass", diff: 0 };
    var band = Math.max(3, Math.round(max * 0.05));
    if (score >= pass - band) return { key: "border", diff: pass - score };
    return { key: "miss", diff: pass - score };
  }

  function verdictShort(res, pass) {
    if (res.key === "pass") return "合格ライン到達！";
    if (res.key === "border") return "ボーダー付近（あと" + res.diff + "点）";
    if (res.key === "miss") return "合格ラインまであと" + res.diff + "点";
    return "自己採点の結果";
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  }

  function drawImage(canvas, data, score, res) {
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height;
    var st = STATE[res.key] || STATE.pass;

    // 背景
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);
    // 外枠
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 2;
    roundRect(ctx, 24, 24, W - 48, H - 48, 28);
    ctx.stroke();
    // 上部アクセントバー
    ctx.fillStyle = ACCENT;
    roundRect(ctx, 24, 24, W - 48, 14, 7);
    ctx.fill();

    ctx.textBaseline = "alphabetic";
    // サイト名
    ctx.fillStyle = ACCENT;
    ctx.font = "700 30px 'Noto Sans JP', sans-serif";
    ctx.fillText("メンタルヘルス・マネジメント検定 解答速報", 70, 110);
    // 試験ラベル
    ctx.fillStyle = "#111827";
    ctx.font = "700 42px 'Noto Sans JP', sans-serif";
    ctx.fillText(data.label + "　" + data.exam, 70, 172);
    ctx.fillStyle = "#6b7280";
    ctx.font = "500 26px 'Noto Sans JP', sans-serif";
    ctx.fillText(data.date + " 実施　自己採点", 70, 214);

    // 得点（大）
    ctx.fillStyle = "#111827";
    ctx.font = "800 150px 'Noto Sans JP', sans-serif";
    var scoreText = String(score);
    ctx.fillText(scoreText, 70, 400);
    var sw = ctx.measureText(scoreText).width;
    ctx.fillStyle = "#6b7280";
    ctx.font = "700 48px 'Noto Sans JP', sans-serif";
    ctx.fillText("/ " + data.max + "点", 70 + sw + 24, 400);
    ctx.font = "500 30px 'Noto Sans JP', sans-serif";
    if (data.pass != null) {
      ctx.fillText("合格ライン " + data.pass + "点", 74, 452);
    }

    // 判定バッジ
    var badge = verdictShort(res, data.pass);
    ctx.font = "800 44px 'Noto Sans JP', sans-serif";
    var bw = ctx.measureText(badge).width + 72;
    var bx = 70, by = 486, bh = 84;
    ctx.fillStyle = st.bg;
    roundRect(ctx, bx, by, Math.min(bw, W - 140), bh, 18);
    ctx.fill();
    ctx.fillStyle = st.color;
    ctx.fillText(badge, bx + 36, by + 56);

    // フッターURL
    ctx.fillStyle = "#9ca3af";
    ctx.font = "500 24px 'Noto Sans JP', sans-serif";
    ctx.fillText("mentalhealth-master.jp", 70, H - 54);
  }

  function shareText(data, score, res) {
    return (
      "【" + data.label + data.exam + " 自己採点】\n" +
      "得点 " + score + "/" + data.max + "点" +
      (data.pass != null ? "（合格ライン" + data.pass + "点）" : "") + "\n" +
      "→ " + verdictShort(res, data.pass)
    );
  }

  function canvasToBlob(canvas) {
    return new Promise(function (resolve) {
      if (canvas.toBlob) canvas.toBlob(resolve, "image/png");
      else {
        var url = canvas.toDataURL("image/png");
        var bin = atob(url.split(",")[1]);
        var arr = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
        resolve(new Blob([arr], { type: "image/png" }));
      }
    });
  }

  function init(root) {
    var data = {
      exam: root.getAttribute("data-exam") || "",
      label: root.getAttribute("data-label") || "",
      max: num(root.getAttribute("data-max")) || 100,
      pass: num(root.getAttribute("data-pass")),
      url: root.getAttribute("data-url") || location.href,
      date: root.getAttribute("data-date") || "",
      hashtags: root.getAttribute("data-hashtags") || ""
    };

    var input = root.querySelector("#sokuhou-score");
    var judgeBtn = root.querySelector("#sokuhou-judge");
    var resultEl = root.querySelector("#sokuhou-result");
    var shareEl = root.querySelector("#sokuhou-share");
    var canvas = root.querySelector("#sokuhou-canvas");
    var nativeBtn = root.querySelector("#sokuhou-share-native");
    var postBtn = root.querySelector("#sokuhou-post-x");
    var saveBtn = root.querySelector("#sokuhou-save-img");

    if (input) input.setAttribute("max", String(data.max));
    var last = null;

    function run() {
      var score = num(input && input.value);
      if (score == null) {
        resultEl.hidden = false;
        resultEl.className = "sokuhou-result is-warn";
        resultEl.textContent = "得点を入力してください。";
        shareEl.hidden = true;
        return;
      }
      if (score < 0) score = 0;
      if (score > data.max) score = data.max;
      var res = judge(score, data.pass, data.max);
      last = { score: score, res: res };

      var st = STATE[res.key] || { label: "自己採点の結果" };
      resultEl.hidden = false;
      resultEl.className = "sokuhou-result is-" + res.key;
      var head = "得点 " + score + " / " + data.max + "点";
      var verdict = verdictShort(res, data.pass);
      resultEl.innerHTML =
        '<span class="sokuhou-result-score">' + head + "</span>" +
        '<span class="sokuhou-result-verdict">' + verdict + "</span>";

      drawImage(canvas, data, score, res);
      shareEl.hidden = false;
    }

    if (judgeBtn) judgeBtn.addEventListener("click", run);
    if (input) input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") { e.preventDefault(); run(); }
    });

    // Web Share API（画像付き）対応端末のみボタン表示
    var canShareFiles = false;
    try {
      canShareFiles = !!(navigator.canShare && navigator.canShare({
        files: [new File([new Blob()], "x.png", { type: "image/png" })]
      }));
    } catch (e) { canShareFiles = false; }
    if (canShareFiles && nativeBtn) nativeBtn.hidden = false;

    if (nativeBtn) nativeBtn.addEventListener("click", function () {
      if (!last) return;
      canvasToBlob(canvas).then(function (blob) {
        var file = new File([blob], "mhm-selfcheck.png", { type: "image/png" });
        var payload = { text: shareText(data, last.score, last.res) + "\n" + data.url };
        try { payload.files = [file]; } catch (e) {}
        if (navigator.canShare && navigator.canShare({ files: [file] })) payload.files = [file];
        navigator.share(payload).catch(function () {});
      });
    });

    if (postBtn) postBtn.addEventListener("click", function () {
      if (!last) { run(); if (!last) return; }
      var text = shareText(data, last.score, last.res);
      var u = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(text) +
        "&url=" + encodeURIComponent(data.url);
      if (data.hashtags) u += "&hashtags=" + encodeURIComponent(data.hashtags);
      window.open(u, "_blank", "noopener");
    });

    if (saveBtn) saveBtn.addEventListener("click", function () {
      if (!last) { run(); if (!last) return; }
      canvasToBlob(canvas).then(function (blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = (data.label || "mhm") + "-自己採点.png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 4000);
      });
    });
  }

  function boot() {
    var nodes = document.querySelectorAll(".sokuhou-selfcheck[data-exam]");
    for (var i = 0; i < nodes.length; i++) init(nodes[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
