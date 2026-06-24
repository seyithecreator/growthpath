// Add show/hide toggle to every password input in the admin
(function () {
  function addToggle(input) {
    if (input.dataset.pwToggled) return;
    input.dataset.pwToggled = '1';

    var wrap = document.createElement('div');
    wrap.style.cssText = 'position:relative;display:block;';
    input.parentNode.insertBefore(wrap, input);
    wrap.appendChild(input);

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.title = 'Show / hide password';
    btn.innerHTML = '&#128065;';
    btn.style.cssText = [
      'position:absolute', 'right:10px', 'top:50%', 'transform:translateY(-50%)',
      'background:none', 'border:none', 'cursor:pointer', 'font-size:16px',
      'opacity:0.6', 'padding:0', 'line-height:1', 'color:inherit',
    ].join(';');

    btn.addEventListener('click', function () {
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      btn.style.opacity = show ? '1' : '0.6';
    });

    wrap.appendChild(btn);
    input.style.paddingRight = '36px';
  }

  function init() {
    document.querySelectorAll('input[type="password"]').forEach(addToggle);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
