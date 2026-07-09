document.querySelectorAll('.chipbar .chip[data-href], .chips .chip[data-href]').forEach(function(c){
  c.addEventListener('click', function(){ location.href = c.dataset.href; });
});
document.querySelectorAll('.sortbar button[data-href]').forEach(function(c){
  c.addEventListener('click', function(){ location.href = c.dataset.href; });
});
