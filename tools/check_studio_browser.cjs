// Local editor-only QA: edits are undone, and no save is submitted.
const fs=require('node:fs'),path=require('node:path');
const {createRequire}=require('node:module');
const {chromium}=createRequire(path.join(process.argv[2],'package.json'))('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.argv[3]||undefined});
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1000}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8772/hub');
  await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('جاهز'));
  const before=await page.evaluate(()=>JSON.stringify(doc));
  await page.selectOption('#tool','rect');
  const box=await page.locator('#scene').boundingBox();
  const point=(x,y)=>({x:box.x+x/1920*box.width,y:box.y+y/1080*box.height});
  const a=point(600,400),b=point(700,450);
  await page.mouse.move(a.x,a.y);await page.mouse.down();await page.mouse.move(b.x,b.y);await page.mouse.up();
  if(!await page.evaluate(()=>doc.colliders.some(r=>Math.abs(r[0]-600)<3&&Math.abs(r[2]-100)<3)))throw Error('Rectangle drawing failed');
  await page.click('#undo');
  if(await page.evaluate(()=>JSON.stringify(doc))!==before)throw Error('Undo did not restore document');
  await page.selectOption('#tool','poly');
  for(const [x,y]of [[650,400],[750,400],[700,500]]){let p=point(x,y);await page.mouse.click(p.x,p.y);}
  await page.keyboard.press('Enter');
  if(!await page.evaluate(()=>doc.polygons.length>0))throw Error('Polygon drawing failed');
  await page.click('#undo');
  await page.selectOption('#tool','select');
  await page.selectOption('#items','0');
  await page.locator('#scene').focus();await page.keyboard.press('ArrowRight');
  if(await page.evaluate(()=>JSON.stringify(doc))===before)throw Error('Precise actor movement failed');
  await page.click('#undo');await page.click('#redo');await page.click('#undo');
  await page.click('#validate');await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('فحص سليم'));
  if(await page.evaluate(()=>JSON.stringify(doc))!==before)throw Error('QA left unsaved changes');
  const output=path.resolve('debug_screenshots/progression');fs.mkdirSync(output,{recursive:true});
  await page.screenshot({path:path.join(output,'hub-studio-1440.png'),fullPage:true});
  await page.setViewportSize({width:1920,height:1080});
  await page.screenshot({path:path.join(output,'hub-studio-1920.png'),fullPage:true});
  if(errors.length)throw Error(errors.join('\n'));
  console.log(JSON.stringify({ok:true,checks:['load','rect drag','polygon','actor nudge','undo','redo','reachability','no saved mutations'],pageErrors:errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
