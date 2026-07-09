function bindChips(groupId, hiddenId, onChange){
  var group = document.getElementById(groupId);
  if(!group) return;
  group.querySelectorAll('.chip').forEach(function(c){
    c.addEventListener('click', function(){
      group.querySelectorAll('.chip').forEach(function(x){ x.classList.remove('on'); });
      c.classList.add('on');
      var hidden = document.getElementById(hiddenId);
      if(hidden) hidden.value = c.dataset.value;
      if(onChange) onChange(c.dataset.value);
    });
  });
}
bindChips('cat-chips', 'f-category');
bindChips('type-chips', 'f-post-type', function(v){
  document.getElementById('profit-row').style.display = v === 'profit' ? 'block' : 'none';
});
bindChips('column-chips', 'f-column-tag');

var photoBtn = document.getElementById('btn-photo');
var fileInput = document.getElementById('f-images');
if(photoBtn && fileInput){
  photoBtn.addEventListener('click', function(){ fileInput.click(); });
  fileInput.addEventListener('change', function(){
    if(fileInput.files.length > 10){
      alert('사진은 최대 10장까지 첨부할 수 있습니다');
      fileInput.value = '';
      return;
    }
    var preview = document.getElementById('img-preview');
    preview.innerHTML = '';
    Array.prototype.forEach.call(fileInput.files, function(f){
      if(f.size > 5 * 1024 * 1024){ alert(f.name + ': 5MB를 초과합니다'); return; }
      var img = document.createElement('img');
      img.style.cssText = 'width:66px;height:66px;object-fit:cover;border-radius:12px';
      img.src = URL.createObjectURL(f);
      preview.appendChild(img);
    });
  });
}
