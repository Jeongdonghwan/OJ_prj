function toggleApi(url, body, cb){
  fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN || ''},
    body: JSON.stringify(body)
  }).then(function(r){
    if(r.status === 401){ location.href = '/login'; return null; }
    return r.json();
  }).then(function(d){ if(d) cb(d); });
}
document.querySelectorAll('.pill.like').forEach(function(b){
  b.addEventListener('click', function(e){
    e.preventDefault(); e.stopPropagation();
    toggleApi('/api/like', {post_id: parseInt(b.dataset.postId, 10)}, function(d){
      b.classList.toggle('liked', d.on);
      var n = b.querySelector('.lc');
      if(n) n.textContent = d.count.toLocaleString();
    });
  });
});
document.querySelectorAll('.pill.scrap').forEach(function(b){
  b.addEventListener('click', function(e){
    e.preventDefault();
    toggleApi('/api/scrap', {post_id: parseInt(b.dataset.postId, 10)}, function(d){
      b.classList.toggle('liked', d.on);
    });
  });
});
document.querySelectorAll('.pill.share').forEach(function(b){
  b.addEventListener('click', function(){
    navigator.clipboard.writeText(location.href).then(function(){ alert('링크가 복사되었습니다'); });
  });
});
document.querySelectorAll('.follow').forEach(function(b){
  b.addEventListener('click', function(){
    toggleApi('/api/follow', {user_id: parseInt(b.dataset.userId, 10)}, function(d){
      b.textContent = d.on ? '팔로잉' : '팔로우';
    });
  });
});
document.querySelectorAll('.cmt .re').forEach(function(b){
  b.addEventListener('click', function(){
    document.getElementById('parent-id').value = b.dataset.commentId;
    var input = document.querySelector('.wr input[name="content"]');
    input.placeholder = '답글을 남겨보세요';
    input.focus();
  });
});
var etcBtn = document.getElementById('etc-btn');
if(etcBtn){
  etcBtn.addEventListener('click', function(){
    if(window.IS_OWNER){
      var act = prompt('1: 수정 / 2: 삭제 / 3: 신고 (번호 입력)');
      if(act === '1'){ location.href = '/write?edit=' + window.POST_ID; }
      else if(act === '2'){
        if(confirm('글을 삭제할까요?')){
          fetch('/post/' + window.POST_ID + '/delete', {method: 'POST', headers: {'X-CSRFToken': window.CSRF_TOKEN || ''}})
            .then(function(){ location.href = '/community'; });
        }
      } else if(act === '3'){ reportPost(); }
    } else {
      reportPost();
    }
  });
}
function reportPost(){
  var reason = prompt('신고 사유를 입력해주세요');
  if(!reason) return;
  toggleApi('/api/report', {target_type: 'post', target_id: window.POST_ID, reason: reason}, function(){
    alert('신고가 접수되었습니다');
  });
}
