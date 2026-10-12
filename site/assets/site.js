(() => {
 const toggle=document.querySelector('.menu-toggle'),menu=document.getElementById('mobile-menu');
 if(!toggle||!menu)return;
 const en=document.documentElement.lang==='en';
 const label=open=>open?(en?'Close menu':'Menüyü kapat'):(en?'Menu':'Menü');
 function close(focus=false){if(menu.hidden)return;menu.hidden=true;toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label',label(false));if(focus)toggle.focus();}
 toggle.addEventListener('click',()=>{const open=menu.hidden;menu.hidden=!open;toggle.setAttribute('aria-expanded',String(open));toggle.setAttribute('aria-label',label(open));if(open)menu.querySelector('a')?.focus();else toggle.focus();});
 menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>close()));
 document.addEventListener('keydown',e=>{if(e.key==='Escape')close(true)});
 document.addEventListener('pointerdown',e=>{if(!menu.hidden&&!menu.contains(e.target)&&!toggle.contains(e.target))close()});
 window.addEventListener('resize',()=>{if(window.innerWidth>1050)close()});
})();