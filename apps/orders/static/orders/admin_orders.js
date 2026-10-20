/* Автообновление админки: опрос новых заказов, баннер и звуковой сигнал. */
(function () {
  var POLL_MS = 25000;
  var lastCount = null;

  function beep() {
    try {
      var Ctx = window.AudioContext || window.webkitAudioContext;
      if (!Ctx) return;
      var ctx = new Ctx();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.type = 'sine';
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.001, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.42);
    } catch (e) { /* звук недоступен — не страшно */ }
  }

  function setBanner(count) {
    var el = document.getElementById('osman-new-banner');
    if (!el) return;
    if (count > 0) {
      el.hidden = false;
      el.innerHTML = '🔔 Новых заказов: ' + count + ' — <a href="?status=new">показать</a>';
    } else {
      el.hidden = true;
    }
  }

  function setTitle(count) {
    var base = document.title.replace(/^🔔 \d+ новых — /, '');
    document.title = count > 0 ? ('🔔 ' + count + ' новых — ' + base) : base;
  }

  function poll() {
    fetch('/api/v1/orders/?status=new&is_spam=false&page_size=1', {credentials: 'same-origin'})
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || typeof data.count === 'undefined') return;
        setBanner(data.count);
        if (lastCount !== null && data.count > lastCount) beep();
        setTitle(data.count);
        lastCount = data.count;
      })
      .catch(function () { /* тихо */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    poll();
    setInterval(poll, POLL_MS);
  });
})();
