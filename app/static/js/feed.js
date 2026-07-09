(function(){
  var container = document.getElementById('feed-items');
  if(!container) return;
  var cursor = window.FEED_NEXT_CURSOR;
  var loading = false;
  function loadMore(){
    if(!cursor || loading) return;
    loading = true;
    var q = window.FEED_QUERY || {};
    var params = new URLSearchParams();
    if(q.cat) params.set('cat', q.cat);
    if(q.sort) params.set('sort', q.sort);
    params.set('cursor', cursor);
    fetch('/api/posts?' + params.toString()).then(function(r){ return r.json(); }).then(function(d){
      d.items.forEach(function(html){
        container.insertAdjacentHTML('beforeend', html);
      });
      cursor = d.next_cursor;
      loading = false;
    });
  }
  window.addEventListener('scroll', function(){
    if(window.innerHeight + window.scrollY >= document.body.offsetHeight - 600) loadMore();
  });
})();
