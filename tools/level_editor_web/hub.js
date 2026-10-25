'use strict';
const $=id=>document.getElementById(id),canvas=$('scene'),ctx=canvas.getContext('2d');
let doc,images={},selected=null,drag=null,points=[],undo=[],redo=[],probe=[960,660],keys=new Set(),dirty=false,pointsKind='select';
const token=document.querySelector('meta[name=editor-token]').content;
const clone=o=>JSON.parse(JSON.stringify(o)),DRAFT='cube-hub-draft-v2';
const status=s=>$('status').textContent=s;
function draft(){try{localStorage.setItem(DRAFT,JSON.stringify({document:doc,points,tool:pointsKind}));}catch(e){status('تعذر حفظ المسودة في المتصفح؛ استخدم تصدير نسخة.');}}
function checkpoint(){dirty=true;undo.push(clone(doc));if(undo.length>80)undo.shift();redo=[];}
window.onbeforeunload=e=>{if(dirty||points.length){e.preventDefault();e.returnValue='';}};
async function api(path,data){
 const r=await fetch(path,{method:data?'POST':'GET',headers:{'X-Editor-Token':token,'Content-Type':'application/json'},body:data?JSON.stringify(data):undefined});
 const b=await r.json();
 if(!r.ok)throw Error((b.errors||[b.error]).join(' / ').replace('Player spawn is inside a wall.','نقطة ظهور اللاعب داخل حاجز. إذا رسمت محيط الأرضية فحوّله إلى أرضية مشي، لا حاجز ممتلئ.'));
 return b;
}
function records(){return [...Object.keys(doc.positions).map(k=>({kind:'npc',key:k,name:doc.npcs[k].label})),{kind:'spawn',name:'ظهور اللاعب'},{kind:'gate',name:'رسم البوابة'},...doc.colliders.map((_,i)=>({kind:'rect',key:i,name:`حاجز ${i+1}`})),...doc.polygons.map((_,i)=>({kind:'poly',key:i,name:`حاجز مضلع ${i+1}`})),...(doc.walkable.length?[{kind:'floor',name:`أرضية مشي / ${doc.walkable.length} نقطة`}]:[])];}
function position(r){return r.kind==='npc'?doc.positions[r.key]:r.kind==='rect'?doc.colliders[r.key]:r.kind==='poly'?doc.polygons[r.key][0]:r.kind==='floor'?doc.walkable[0]:doc[r.kind];}
function shift(r,dx,dy){if(r.kind==='poly'||r.kind==='floor'){for(const v of r.kind==='floor'?doc.walkable:doc.polygons[r.key]){v[0]+=dx;v[1]+=dy;}}else{const p=position(r);p[0]+=dx;p[1]+=dy;}}
function refresh(){const list=records();$('items').replaceChildren(...list.map((r,i)=>{const o=document.createElement('option');o.textContent=r.name;o.value=i;return o;}));if(selected)$('items').value=list.findIndex(r=>r.kind===selected.kind&&r.key===selected.key);properties();draw();}
function properties(){
 const area=$('properties');area.replaceChildren();if(!selected)return;const p=position(selected);
 for(const [i,label]of ['X','Y',...(selected.kind==='rect'?['عرض','ارتفاع']:[])].entries()){
  const l=document.createElement('label');l.textContent=label;const n=document.createElement('input');n.type='number';n.value=p[i];
  n.onchange=()=>{checkpoint();if(i<2)shift(selected,i===0?Number(n.value)-p[0]:0,i===1?Number(n.value)-p[1]:0);else p[i]=Number(n.value);draft();draw();};l.append(n);area.append(l);
 }
}
function trace(poly){poly.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.closePath();}
function draw(){
 if(!doc)return;ctx.clearRect(0,0,1920,1080);if(images.bg)ctx.drawImage(images.bg,0,0,1920,1080);
 if($('overlay').checked){
  if(doc.walkable.length){ctx.beginPath();ctx.rect(0,0,1920,1080);trace(doc.walkable);ctx.fillStyle='#ee53636b';ctx.fill('evenodd');ctx.beginPath();trace(doc.walkable);ctx.strokeStyle='#6bffb2';ctx.lineWidth=4;ctx.stroke();}
  ctx.fillStyle='#f65b6650';ctx.strokeStyle='#ff8b92';ctx.lineWidth=3;
  for(const r of doc.colliders){ctx.fillRect(...r);ctx.strokeRect(...r);}for(const p of doc.polygons){ctx.beginPath();trace(p);ctx.fill();ctx.stroke();}
 }
 for(const [role,p]of Object.entries(doc.positions)){
  const cfg=doc.npcs[role],im=images[role];if(im)ctx.drawImage(im,p[0]+23-cfg.size[0]/2,p[1]+46-cfg.size[1],...cfg.size);
  if($('overlay').checked){ctx.strokeStyle='#6fe9ff';ctx.strokeRect(p[0],p[1],46,46);ctx.beginPath();ctx.arc(p[0]+23,p[1]+23,110,0,Math.PI*2);ctx.stroke();}
  ctx.font='20px Arial';ctx.fillStyle='#edfaff';ctx.fillText(role==='portal'?'Gate interaction':cfg.label,p[0]-20,p[1]+75);
 }
 ctx.fillStyle='#ffe178';ctx.fillRect(doc.gate[0],doc.gate[1],90,6);ctx.font='20px Arial';ctx.fillText('Gate art',doc.gate[0],doc.gate[1]-8);ctx.strokeStyle='#79ffc0';ctx.strokeRect(doc.spawn[0]-20,doc.spawn[1]-20,40,40);
 if(selected){const p=position(selected);ctx.strokeStyle='#ffed80';ctx.lineWidth=5;ctx.strokeRect(p[0]-6,p[1]-6,selected.kind==='rect'?p[2]+12:58,selected.kind==='rect'?p[3]+12:58);}
 if(points.length){ctx.beginPath();points.forEach(([x,y],i)=>i?ctx.lineTo(x,y):ctx.moveTo(x,y));ctx.strokeStyle='#ffe178';ctx.stroke();for(const [x,y]of points){ctx.fillStyle='#fff2aa';ctx.fillRect(x-4,y-4,8,8);}ctx.beginPath();ctx.arc(...points[0],12,0,Math.PI*2);ctx.stroke();}
 if(drag?.newRect){ctx.strokeStyle='#fff2aa';ctx.strokeRect(drag.start[0],drag.start[1],drag.end[0]-drag.start[0],drag.end[1]-drag.start[1]);}
 if($('tool').value==='test'){ctx.fillStyle='#76ffbf';ctx.fillRect(probe[0]-20,probe[1]-20,40,40);}
 $('pending').textContent=points.length?`${points.length}/512 نقطة غير معتمدة — انقر أول نقطة أو «إنهاء الرسم»`:'الأخضر: داخل أرضية المشي مسموح / الأحمر: ممنوع';$('finish').disabled=points.length<3;
}
function pointer(e){const r=canvas.getBoundingClientRect(),s=Number($('snap').value);return [Math.max(0,Math.min(1920,Math.round((e.clientX-r.left)*1920/r.width/s)*s)),Math.max(0,Math.min(1080,Math.round((e.clientY-r.top)*1080/r.height/s)*s))];}
function inside([x,y],poly){let yes=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>y)!==(b[1]>y)&&x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0])yes=!yes;}return yes;}
function hit(p){const entries=records();return entries.filter(r=>r.kind!=='floor').reverse().find(r=>{const q=position(r);if(r.kind==='rect')return p[0]>=q[0]&&p[0]<=q[0]+q[2]&&p[1]>=q[1]&&p[1]<=q[1]+q[3];if(r.kind==='poly')return inside(p,doc.polygons[r.key]);return Math.hypot(p[0]-q[0]-(r.kind==='npc'?23:0),p[1]-q[1]-(r.kind==='npc'?23:0))<55;})||(doc.walkable.length&&inside(p,doc.walkable)?{kind:'floor',name:'أرضية المشي'}:null);}
function finish(kind=$('tool').value){
 if(points.length<3){status('أضف ثلاث نقاط على الأقل.');return false;}
 const poly=clone(points);if(poly.length>3&&Math.hypot(poly[0][0]-poly.at(-1)[0],poly[0][1]-poly.at(-1)[1])<1)poly.pop();checkpoint();
 if(kind==='floor'){doc.walkable=poly;selected={kind:'floor'};}else{doc.polygons.push(poly);selected={kind:'poly',key:doc.polygons.length-1};}
 points=[];draft();refresh();status(kind==='floor'?'اعتمدت أرضية المشي: الداخل مسموح والخارج ممنوع. افحص ثم احفظ.':'اعتمد الحاجز الممتلئ: داخله ممنوع. لتحديد محيط الماب استخدم «تحويل إلى أرضية مشي».');return true;
}
canvas.onpointerdown=e=>{
 canvas.focus();const p=pointer(e),tool=$('tool').value;if(['poly','floor'].includes(tool)){
  if(points.length>=3&&Math.hypot(p[0]-points[0][0],p[1]-points[0][1])<=12){finish();return;}
  if(points.length>=512){status('وصلت إلى 512 نقطة؛ أنهِ الرسم.');return;}pointsKind=tool;points.push(p);dirty=true;draft();draw();return;
 }
 if(tool==='test')return;if(tool==='rect')drag={newRect:true,start:p,end:p};else{selected=hit(p);if(selected){checkpoint();drag={start:p,last:p};}refresh();}canvas.setPointerCapture(e.pointerId);
};
canvas.onpointermove=e=>{if(!drag)return;const p=pointer(e);if(drag.newRect)drag.end=p;else{shift(selected,p[0]-drag.last[0],p[1]-drag.last[1]);drag.last=p;}draft();draw();};
canvas.onpointerup=()=>{if(drag?.newRect){const [a,b]=[drag.start,drag.end],r=[Math.min(a[0],b[0]),Math.min(a[1],b[1]),Math.abs(a[0]-b[0]),Math.abs(a[1]-b[1])];if(r[2]>=8&&r[3]>=8){checkpoint();doc.colliders.push(r);selected={kind:'rect',key:doc.colliders.length-1};}}drag=null;draft();refresh();};
$('items').onchange=()=>{selected=records()[Number($('items').value)];properties();draw();};
function remove(){if(!selected||!['rect','poly','floor'].includes(selected.kind))return;checkpoint();if(selected.kind==='floor')doc.walkable=[];else doc[selected.kind==='rect'?'colliders':'polygons'].splice(selected.key,1);selected=null;draft();refresh();}
$('remove').onclick=remove;$('finish').onclick=()=>finish();
$('asFloor').onclick=()=>{if(points.length>=3){finish('floor');return;}if(selected?.kind!=='poly'){status('اختر حاجزًا مضلعًا من القائمة، أو ارسم المحيط أولًا.');return;}checkpoint();doc.walkable=doc.polygons.splice(selected.key,1)[0];selected={kind:'floor'};draft();refresh();status('حوّل المضلع إلى أرضية مشي: الخارج ممنوع، والداخل مسموح.');};
function history(from,to){if(!from.length)return;dirty=true;to.push(clone(doc));doc=from.pop();selected=null;draft();refresh();}
$('undo').onclick=()=>history(undo,redo);$('redo').onclick=()=>history(redo,undo);
for(const action of ['validate','save','play'])$(action).onclick=async()=>{
 try{if(points.length&&!finish())return;status('جاري الفحص…');await api(`/api/hub/${action}`,{document:doc});if(action!=='validate'){dirty=false;localStorage.removeItem(DRAFT);}status(action==='validate'?'فحص سليم: نقطة الظهور وكل الشخصيات قابلة للوصول.':action==='play'?'تم الحفظ وتشغيل الهوب المكتبي.':'تم الحفظ مع نسخة احتياطية.');}catch(e){status(e.message);}
};
$('overlay').onchange=draw;$('tool').onchange=()=>{if(points.length){status('الرسم الجاري محفوظ كمسودة. أنهِه قبل تغيير الأداة.');$('tool').value=pointsKind;return;}pointsKind=$('tool').value;probe=[...doc.spawn];draw();};
canvas.onkeydown=e=>{
 keys.add(e.key.toLowerCase());if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' ','Delete','Enter','Backspace'].includes(e.key))e.preventDefault();
 if(e.key==='Escape'){points=[];drag=null;draft();draw();}if(e.key==='Backspace'&&points.length){points.pop();draft();draw();}if(e.key==='Enter'&&points.length>=3)finish();if(e.key==='Delete')remove();
 if(selected&&e.key.startsWith('Arrow')){checkpoint();const n=e.shiftKey?10:1;shift(selected,e.key==='ArrowLeft'?-n:e.key==='ArrowRight'?n:0,e.key==='ArrowUp'?-n:e.key==='ArrowDown'?n:0);draft();properties();draw();}
};canvas.onkeyup=e=>keys.delete(e.key.toLowerCase());canvas.onblur=()=>keys.clear();
function blocked(p){
 const x=p[0]-20,y=p[1]-20,corners=[[x,y],[x+40,y],[x,y+40],[x+40,y+40]];
 if(x<0||y<0||x+40>1920||y+40>1080)return true;if(doc.walkable.length&&corners.some(q=>!inside(q,doc.walkable)))return true;
 const solids=[...doc.colliders,...Object.values(doc.positions).map(v=>[...v,46,46]),[...doc.gate,90,90]];if(solids.some(r=>x<r[0]+r[2]&&x+40>r[0]&&y<r[1]+r[3]&&y+40>r[1]))return true;
 return doc.polygons.some(poly=>[...corners,p].some(q=>inside(q,poly))||poly.some(([px,py])=>px>=x&&px<=x+40&&py>=y&&py<=y+40));
}
let last=performance.now();function tick(now){const dt=Math.min(.04,(now-last)/1000);last=now;if(doc&&$('tool').value==='test'){const dx=Number(keys.has('d'))-Number(keys.has('a')),dy=Number(keys.has('s'))-Number(keys.has('w')),n=Math.hypot(dx,dy)||1;let p=[probe[0]+dx/n*300*dt,probe[1]];if(!blocked(p))probe=p;p=[probe[0],probe[1]+dy/n*300*dt];if(!blocked(p))probe=p;draw();}requestAnimationFrame(tick);}requestAnimationFrame(tick);
function restore(data){
 if(!data?.document?.positions||!Array.isArray(data.document.polygons)||!Array.isArray(data.points||[]))throw Error('ملف المسودة غير صالح.');
 checkpoint();doc=clone(data.document);doc.walkable||=[];points=clone(data.points||[]);selected=null;pointsKind=data.tool||'floor';$('tool').value=points.length?pointsKind:'select';probe=[...doc.spawn];draft();refresh();status(points.length?'استعدت نقاط الرسم. اضغط «تحويل إلى أرضية مشي» ثم افحص واحفظ.':'استعيدت المسودة؛ افحص قبل الحفظ.');
}
$('restore').onclick=()=>{try{const text=localStorage.getItem(DRAFT);if(!text){status('لا توجد مسودة محلية لهذا المنفذ. يمكنك استيراد ملف من منفذ آخر.');return;}restore(JSON.parse(text));}catch(e){status(e.message);}};
$('export').onclick=()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify({document:doc,points,tool:pointsKind},null,2)],{type:'application/json'}));a.download='cube-hub-draft.json';a.click();URL.revokeObjectURL(a.href);status('صدّرت نسخة من البيانات والنقاط الجارية؛ ليست حفظًا داخل اللعبة.');};
$('import').onchange=async e=>{try{restore(JSON.parse(await e.target.files[0].text()));}catch(error){status(error.message);}e.target.value='';};
async function image(path){const im=new Image();im.src='/object-art?file='+encodeURIComponent(path);await im.decode();return im;}
(async()=>{
 try{doc=(await api('/api/hub')).document;doc.walkable||=[];images.bg=await image(doc.background);
  for(const [role,cfg]of Object.entries(doc.npcs)){if(!cfg.art)continue;const im=await image(cfg.art),c=document.createElement('canvas');c.width=im.width;c.height=im.height;const g=c.getContext('2d');g.drawImage(im,0,0);const pixels=g.getImageData(0,0,c.width,c.height).data;let l=c.width,t=c.height,r=0,b=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(pixels[(y*c.width+x)*4+3]>=16){l=Math.min(l,x);t=Math.min(t,y);r=Math.max(r,x);b=Math.max(b,y);}images[role]=await createImageBitmap(im,l,t,r-l+1,b-t+1);}
  refresh();status(localStorage.getItem(DRAFT)?'توجد مسودة غير محفوظة؛ اضغط «استعادة المسودة» لاسترجاعها.':'لتحديد الماب اختر «حدود أرضية المشي»: الداخل مسموح والخارج ممنوع.');
 }catch(e){status(e.message);}
})();
