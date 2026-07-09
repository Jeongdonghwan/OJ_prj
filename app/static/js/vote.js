document.querySelectorAll('.vtbox .vtb').forEach(function(btn){
  btn.addEventListener('click', function(){
    var w = btn.closest('.vtbox');
    if(w.classList.contains('done')) return;
    fetch('/api/poll/vote', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN || ''},
      body: JSON.stringify({poll_id: parseInt(w.dataset.pollId, 10), side: btn.dataset.side})
    }).then(function(r){
      if(r.status === 401){ location.href = '/login'; return null; }
      return r.json();
    }).then(function(d){
      if(!d) return;
      w.classList.add('done');
      btn.classList.add('picked');
      var bars = w.querySelectorAll('.vbar');
      if(d.up_pct !== undefined){
        bars[0].querySelector('.fill').style.width = d.up_pct + '%';
        bars[0].querySelector('b').textContent = d.up_pct + '%';
        bars[1].querySelector('.fill').style.width = d.down_pct + '%';
        bars[1].querySelector('b').textContent = d.down_pct + '%';
        w.querySelector('.vtn').textContent = d.total.toLocaleString() + '명 참여 · 매일 자정 마감';
      }
      w.querySelector('.vtr').style.display = 'block';
    });
  });
});
