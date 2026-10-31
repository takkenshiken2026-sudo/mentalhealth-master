/* 解答速報：自己採点（問題ごとに解答を入力 → 本サイト独自解答で採点 → 結果画像を X シェア）
 * - 解答データは #sokuhou-answers（application/json）に埋め込み。空なら何もしない。
 * - 入力した解答は端末内でのみ処理（送信・保存なし）。
 * - 画像は <canvas> 生成。X の web intent は画像を自動添付できないため、保存＋手動添付、
 *   またはスマホの Web Share API（画像付き共有）に対応。
 */
(function () {
  "use strict";

  var ACCENT = "#4a6b5c";
  var STATE = {
    pass: { color: "#1f7a4d", bg: "#e7f4ec" },
    border: { color: "#9a6a00", bg: "#fbf1dc" },
    miss: { color: "#8a3d3d", bg: "#f7e9e9" }
  };

  function num(v) {
    var n = parseInt(String(v).replace(/[^0-9-]/g, ""), 10);
    return isNaN(n) ? null : n;
  }

  function judge(score, pass, total) {
    if (pass == null) return { key: "none" };
    if (score >= pass) return { key: "pass", diff: 0 };
    var band = Math.max(3, Math.round(total * 0.05));
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

  function drawImage(canvas, data, r) {
    var ctx = canvas.getContext("2d");
    var W = canvas.width, H = canvas.height;
    var st = STATE[r.res.key] || STATE.pass;

    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 2;
    roundRect(ctx, 16, 16, W - 32, H - 32, 26);
    ctx.stroke();
    ctx.fillStyle = ACCENT;
    roundRect(ctx, 16, 16, W - 32, 12, 6);
    ctx.fill();

    ctx.textBaseline = "alphabetic";
    ctx.textAlign = "left";
    // ヘッダー
    ctx.fillStyle = ACCENT;
    ctx.font = "700 28px 'Noto Sans JP', sans-serif";
    ctx.fillText("メンタルヘルス・マネジメント検定 解答速報", 60, 92);
    ctx.fillStyle = "#111827";
    ctx.font = "700 40px 'Noto Sans JP', sans-serif";
    ctx.fillText(data.label + "　" + data.exam, 60, 150);
    ctx.fillStyle = "#6b7280";
    ctx.font = "500 24px 'Noto Sans JP', sans-serif";
    ctx.fillText(data.date + " 実施　自己採点", 60, 188);

    // 得点（大）
    ctx.fillStyle = "#111827";
    ctx.font = "800 120px 'Noto Sans JP', sans-serif";
    var scoreText = String(r.score);
    ctx.fillText(scoreText, 60, 330);
    var sw = ctx.measureText(scoreText).width;
    ctx.fillStyle = "#6b7280";
    ctx.font = "700 40px 'Noto Sans JP', sans-serif";
    ctx.fillText("/ " + r.total + "点", 60 + sw + 20, 330);
    ctx.font = "500 26px 'Noto Sans JP', sans-serif";
    var sub = "正答 " + r.correct + "/" + r.n + "問";
    if (data.pass != null) sub += "　合格ライン " + data.pass + "点";
    ctx.fillText(sub, 62, 372);

    // 判定バッジ（右上）
    var badge = verdictShort(r.res, data.pass);
    ctx.font = "800 40px 'Noto Sans JP', sans-serif";
    var bw = ctx.measureText(badge).width + 56;
    var bh = 76, by = 250, bx = W - 60 - bw;
    ctx.fillStyle = st.bg;
    roundRect(ctx, bx, by, bw, bh, 16);
    ctx.fill();
    ctx.fillStyle = st.color;
    ctx.fillText(badge, bx + 28, by + 50);

    // 回答一覧の見出し＋凡例
    ctx.fillStyle = "#111827";
    ctx.font = "700 26px 'Noto Sans JP', sans-serif";
    var headTxt = "回答一覧（あなたの解答と正答）";
    ctx.fillText(headTxt, 60, 428);
    var lx = 60 + ctx.measureText(headTxt).width + 28, ly = 410;
    var legend = [["#e7f4ec", "#1f7a4d", "正解"], ["#f7e9e9", "#8a3d3d", "不正解"], ["#eef0f2", "#6b7280", "未回答"]];
    ctx.font = "500 20px 'Noto Sans JP', sans-serif";
    for (var li = 0; li < legend.length; li++) {
      ctx.fillStyle = legend[li][0]; roundRect(ctx, lx, ly, 22, 22, 5); ctx.fill();
      ctx.strokeStyle = legend[li][1]; ctx.lineWidth = 1; roundRect(ctx, lx, ly, 22, 22, 5); ctx.stroke();
      ctx.fillStyle = "#374151"; ctx.fillText(legend[li][2], lx + 30, ly + 18);
      lx += 30 + ctx.measureText(legend[li][2]).width + 24;
    }
    // 各セルの見方
    ctx.fillStyle = "#6b7280"; ctx.font = "500 18px 'Noto Sans JP', sans-serif"; ctx.textAlign = "left";
    ctx.fillText("「答」＝あなたの解答　「正」＝正答", 60, 458);

    // 回答グリッド（10列×5行）：各問に あなたの解答 と 正答 を併記
    var detail = r.detail || [];
    var cols = 10, cw = 100, ch = 62, gx = 8, gy = 8, ox = 60, oy = 478;
    for (var i = 0; i < detail.length; i++) {
      var d = detail[i];
      var col = i % cols, row = Math.floor(i / cols);
      var x = ox + col * (cw + gx), y = oy + row * (ch + gy);
      var bg = d.blank ? "#eef0f2" : (d.ok ? "#e7f4ec" : "#f7e9e9");
      var bd = d.blank ? "#d1d5db" : (d.ok ? "#bfe3cd" : "#e9c6c6");
      ctx.fillStyle = bg; roundRect(ctx, x, y, cw, ch, 9); ctx.fill();
      ctx.strokeStyle = bd; ctx.lineWidth = 1; roundRect(ctx, x, y, cw, ch, 9); ctx.stroke();
      // 問番号（左上）
      ctx.fillStyle = "#6b7280"; ctx.font = "700 15px 'Noto Sans JP', sans-serif"; ctx.textAlign = "left";
      ctx.fillText(String(d.no), x + 9, y + 21);
      // あなたの解答（答 X）
      ctx.textAlign = "right";
      ctx.fillStyle = "#9ca3af"; ctx.font = "500 14px 'Noto Sans JP', sans-serif";
      ctx.fillText("答", x + cw - 42, y + 25);
      ctx.fillStyle = d.blank ? "#9ca3af" : (d.ok ? "#1f7a4d" : "#8a3d3d");
      ctx.font = "800 22px 'Noto Sans JP', sans-serif";
      ctx.fillText(d.blank ? "—" : String(d.user), x + cw - 12, y + 27);
      // 正答（正 Y）
      ctx.fillStyle = "#9ca3af"; ctx.font = "500 14px 'Noto Sans JP', sans-serif";
      ctx.fillText("正", x + cw - 42, y + 52);
      ctx.fillStyle = "#374151"; ctx.font = "800 22px 'Noto Sans JP', sans-serif";
      ctx.fillText(String(d.correct), x + cw - 12, y + 54);
      ctx.textAlign = "left";
    }

    ctx.fillStyle = "#9ca3af";
    ctx.font = "500 22px 'Noto Sans JP', sans-serif"; ctx.textAlign = "left";
    ctx.fillText("mentalhealth-master.jp", 60, H - 34);
  }

  function shareText(data, r) {
    return (
      "【" + data.label + data.exam + " 自己採点】\n" +
      "得点 " + r.score + "/" + r.total + "点（正答 " + r.correct + "/" + r.n + "問）\n" +
      "→ " + verdictShort(r.res, data.pass)
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
    var answers = [];
    var dataEl = root.querySelector("#sokuhou-answers");
    if (dataEl) {
      try { answers = JSON.parse(dataEl.textContent || "[]"); } catch (e) { answers = []; }
    }
    if (!answers.length) return; // データ未投入（準備中表示）

    var data = {
      exam: root.getAttribute("data-exam") || "",
      label: root.getAttribute("data-label") || "",
      pass: num(root.getAttribute("data-pass")),
      url: root.getAttribute("data-url") || location.href,
      date: root.getAttribute("data-date") || "",
      hashtags: root.getAttribute("data-hashtags") || ""
    };
    var total = 0;
    for (var i = 0; i < answers.length; i++) total += (answers[i].points || 0);

    var grid = root.querySelector("#sokuhou-grid");
    var judgeBtn = root.querySelector("#sokuhou-judge");
    var clearBtn = root.querySelector("#sokuhou-clear");
    var resultEl = root.querySelector("#sokuhou-result");
    var shareEl = root.querySelector("#sokuhou-share");
    var canvas = root.querySelector("#sokuhou-canvas");
    var nativeBtn = root.querySelector("#sokuhou-share-native");
    var postBtn = root.querySelector("#sokuhou-post-x");
    var saveBtn = root.querySelector("#sokuhou-save-img");

    var picks = {}; // no -> selected choice (string)
    var last = null;

    // 問題グリッド生成
    answers.forEach(function (a) {
      var cell = document.createElement("div");
      cell.className = "sokuhou-q";
      cell.setAttribute("data-no", a.no);
      var label = document.createElement("div");
      label.className = "sokuhou-q-label";
      label.textContent = a.label || ("問" + a.no);
      cell.appendChild(label);
      var choices = document.createElement("div");
      choices.className = "sokuhou-choices";
      var n = a.choices || 4;
      for (var c = 1; c <= n; c++) {
        (function (c) {
          var btn = document.createElement("button");
          btn.type = "button";
          btn.className = "sokuhou-choice";
          btn.textContent = String(c);
          btn.setAttribute("aria-label", "問" + a.no + " 選択肢" + c);
          btn.addEventListener("click", function () {
            var all = choices.querySelectorAll(".sokuhou-choice");
            for (var k = 0; k < all.length; k++) all[k].classList.remove("is-selected");
            btn.classList.add("is-selected");
            picks[a.no] = String(c);
          });
          choices.appendChild(btn);
        })(c);
      }
      cell.appendChild(choices);
      var mark = document.createElement("span");
      mark.className = "sokuhou-q-mark";
      cell.appendChild(mark);
      grid.appendChild(cell);
    });

    function grade() {
      var score = 0, correct = 0, answered = 0;
      var detail = [];
      answers.forEach(function (a) {
        var sel = picks[a.no];
        var cell = grid.querySelector('.sokuhou-q[data-no="' + a.no + '"]');
        var mark = cell.querySelector(".sokuhou-q-mark");
        cell.classList.remove("is-correct", "is-wrong", "is-blank");
        var blank = (sel == null), ok = false;
        if (blank) {
          cell.classList.add("is-blank");
          mark.textContent = "未";
        } else {
          answered++;
          if (String(sel) === String(a.correct)) {
            score += (a.points || 0); correct++; ok = true;
            cell.classList.add("is-correct"); mark.textContent = "○";
          } else {
            cell.classList.add("is-wrong"); mark.textContent = "×→" + a.correct;
          }
        }
        detail.push({ no: a.no, user: blank ? null : sel, correct: a.correct, ok: ok, blank: blank });
      });
      var res = judge(score, data.pass, total);
      last = { score: score, total: total, correct: correct, n: answers.length, answered: answered, res: res, detail: detail };

      resultEl.hidden = false;
      resultEl.className = "sokuhou-result is-" + res.key;
      resultEl.innerHTML =
        '<span class="sokuhou-result-score">得点 ' + score + " / " + total + "点" +
        '<span class="sokuhou-result-sub">（正答 ' + correct + "/" + answers.length + "問" +
        (answered < answers.length ? "・未解答 " + (answers.length - answered) + "問" : "") + "）</span></span>" +
        '<span class="sokuhou-result-verdict">' + verdictShort(res, data.pass) + "</span>";

      drawImage(canvas, data, last);
      shareEl.hidden = false;
      resultEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    function clearAll() {
      picks = {};
      last = null;
      var sel = grid.querySelectorAll(".sokuhou-choice.is-selected");
      for (var i = 0; i < sel.length; i++) sel[i].classList.remove("is-selected");
      var cells = grid.querySelectorAll(".sokuhou-q");
      for (var j = 0; j < cells.length; j++) {
        cells[j].classList.remove("is-correct", "is-wrong", "is-blank");
        var m = cells[j].querySelector(".sokuhou-q-mark");
        if (m) m.textContent = "";
      }
      resultEl.hidden = true;
      shareEl.hidden = true;
    }

    if (judgeBtn) judgeBtn.addEventListener("click", grade);
    if (clearBtn) clearBtn.addEventListener("click", clearAll);

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
        var payload = { text: shareText(data, last) + "\n" + data.url };
        if (navigator.canShare && navigator.canShare({ files: [file] })) payload.files = [file];
        navigator.share(payload).catch(function () {});
      });
    });

    if (postBtn) postBtn.addEventListener("click", function () {
      if (!last) { grade(); if (!last) return; }
      var u = "https://twitter.com/intent/tweet?text=" + encodeURIComponent(shareText(data, last)) +
        "&url=" + encodeURIComponent(data.url);
      if (data.hashtags) u += "&hashtags=" + encodeURIComponent(data.hashtags);
      window.open(u, "_blank", "noopener");
    });

    if (saveBtn) saveBtn.addEventListener("click", function () {
      if (!last) { grade(); if (!last) return; }
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
