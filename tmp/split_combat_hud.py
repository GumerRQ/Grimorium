from pathlib import Path
from PIL import Image
import json
source=Path('assets/images/backgrounds/tower/combat_hud.png')
im=Image.open(source).convert('RGBA')
out=Path('assets/images/hud/panels');out.mkdir(parents=True,exist_ok=True)
parts={}
for key,bounds in [('stats_panel',(0,0,320,360)),('tower_panel',(320,0,640,360))]:
 region=im.crop(bounds);box=region.getchannel('A').getbbox()
 actual=(box[0]+bounds[0],box[1],box[2]+bounds[0],box[3])
 name={'stats_panel':'stats_panel.png','tower_panel':'tower_panel.png'}[key]
 dest=out/name
 if dest.exists():raise RuntimeError(f'Refusing to replace existing artwork: {dest}')
 im.crop(actual).save(dest)
 parts[key]={'rect':[actual[0],actual[1],actual[2]-actual[0],actual[3]-actual[1]],'asset':'images/hud/panels/'+name}
print(json.dumps(parts))
Path('tmp/hud_panel_crops.json').write_text(json.dumps(parts),encoding='utf-8')
