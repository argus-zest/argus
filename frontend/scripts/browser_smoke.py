from playwright.sync_api import sync_playwright, expect
from pathlib import Path
import json
out=Path('.cache/security-layout');out.mkdir(exist_ok=True)
results=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True)
 for width,height in [(1440,900),(390,844),(768,1024),(1024,768)]:
  page=b.new_page(viewport={'width':width,'height':height});page.set_default_timeout(10000)
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto('http://127.0.0.1:5173/?demo=1',wait_until='domcontentloaded')
  page.get_by_role('status').filter(has_text='Local mock data').wait_for()
  bounds=page.evaluate('''() => ({overflow:document.documentElement.scrollWidth>innerWidth, nav:[...document.querySelectorAll('header button')].map(e=>({text:e.textContent,rect:e.getBoundingClientRect().toJSON()})), map:document.querySelector('canvas.maplibregl-canvas').getBoundingClientRect().toJSON(), panels:[...document.querySelectorAll('aside')].map(e=>e.getBoundingClientRect().toJSON())})''')
  assert not bounds['overflow'],bounds
  assert all(v['rect']['left']>=0 and v['rect']['right']<=width for v in bounds['nav']),bounds
  assert bounds['map']['width']>=320 and bounds['map']['height']>=360,bounds
  assert bounds['map']['right']<=width,bounds
  assert all(v['width']>=320 and v['right']<=width for v in bounds['panels']),bounds
  page.screenshot(path=str(out/f'after-{width}.png'),full_page=width<1280)
  for name,heading in [('Report Hazard','Report Road Hazard'),('Cases','Escalation & Case Workflow'),('Model & Evidence','Model Specification & Evidence'),('Architecture','Argus System Architecture')]:
   page.get_by_role('button',name=name,exact=True).click();page.get_by_role('heading',name=heading,exact=True).wait_for()
   if width==390:page.screenshot(path=str(out/f'modal-{name.split()[0]}.png'))
   assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
   page.reload(wait_until='domcontentloaded');page.get_by_role('button').filter(has_text='Minto Bridge').first.wait_for()
  spot=page.get_by_role('button').filter(has_text='Minto Bridge').first;expect(spot).to_contain_text('14%');base=spot.inner_text()
  page.get_by_role('button').filter(has_text='Cloudburst').click();expect(spot).to_contain_text('94%')
  assert spot.inner_text()!=base
  page.keyboard.press('0');expect(spot).to_contain_text('14%');assert spot.inner_text()==base
  assert not errors,errors
  print(width,'layout, navigation, fallback map, four panels, scenario and shortcut passed')
  results.append({'width':width,'height':height,'bounds':bounds,'page_errors':errors});page.close()
 # Test actual MapLibre attribution sanitization without a deployed backend or third-party style.
 page=b.new_page();page.goto('http://127.0.0.1:5173',wait_until='domcontentloaded')
 result=page.evaluate('''async () => {
  const ml=await import('/node_modules/.vite/deps/maplibre-gl.js');
  const host=document.createElement('div');host.style.cssText='width:400px;height:300px';document.body.append(host);
  window.__attributionExecuted=false;
  const map=new ml.Map({container:host,attributionControl:false,style:{version:8,sources:{},layers:[]}});
  map.addControl(new ml.AttributionControl({compact:false,customAttribution:'<details open onload="window.__attributionExecuted=true" ontoggle="window.__attributionExecuted=true">security fixture</details>'}));
  await new Promise(resolve=>setTimeout(resolve,100));
  const attribution=host.querySelector('.maplibregl-ctrl-attrib-inner');
  const result={executed:window.__attributionExecuted,html:attribution?.innerHTML};map.remove();host.remove();return result;
 }''')
 assert not result['executed'] and 'ontoggle' not in result['html'] and 'onload' not in result['html'],result
 print('Actual MapLibre untrusted attribution fixture: dangerous attributes removed, no execution')
 (out/'after-results.json').write_text(json.dumps({'layouts':results,'maplibre_sanitization':result},indent=2))
 b.close()
