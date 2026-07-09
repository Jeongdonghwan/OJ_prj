function qzHist(btn){
  var h = btn.closest('.qzbox').querySelector('.qzhist');
  var open = h.style.display === 'block';
  h.style.display = open ? 'none' : 'block';
  btn.textContent = open ? '지난 퀴즈 보기' : '지난 퀴즈 접기';
}
document.querySelectorAll('.qzbox .qzb').forEach(function(btn){
  btn.addEventListener('click', function(){
    var w = btn.closest('.qzbox');
    if(w.classList.contains('done')) return;
    fetch('/api/quiz/answer', {
      method: 'POST',
      headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN || ''},
      body: JSON.stringify({quiz_id: parseInt(w.dataset.quizId, 10), choice_no: parseInt(btn.dataset.no, 10)})
    }).then(function(r){
      if(r.status === 401){ location.href = '/login'; return null; }
      return r.json();
    }).then(function(d){
      if(!d) return;
      w.classList.add('done');
      btn.classList.add(d.is_correct ? 'ok' : 'no');
      var a = w.querySelector('.qza');
      a.style.display = 'block';
      a.innerHTML = '<b>' + (d.is_correct ? '정답! ' : '아쉬워요. ') + '정답은 ' + a.dataset.ans + '</b><br>' + a.dataset.exp;
    });
  });
});
