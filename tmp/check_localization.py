import ast,json,re
from pathlib import Path
root=Path.cwd()
for lang in ('es','en'):
 p=root/'data/lang'/f'{lang}.json';d=json.loads(p.read_text(encoding='utf-8'))
 d['ui']['shop'].update(dict(zip(('powers','potions','books','spells'),('Poderes','Pociones','Libros','Hechizos') if lang=='es' else ('Powers','Potions','Books','Spells'))))
 if lang=='es':
  fixes={'menu':'menú','Raton':'Ratón','basico':'básico','COMO JUGAR':'CÓMO JUGAR','Si':'Sí','maximo':'máximo'}
  def accents(v):
   if isinstance(v,dict):return {k:accents(x) for k,x in v.items()}
   if isinstance(v,str):
    for a,b in fixes.items():v=re.sub(r'\b'+re.escape(a)+r'\b',b,v)
   return v
  d['ui']=accents(d['ui'])
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def flatten(d,prefix=''):
 out={}
 for k,v in d.items():
  key=prefix+k
  if isinstance(v,dict):out.update(flatten(v,key+'.'))
  else:out[key]=v
 return out
es=flatten(json.loads((root/'data/lang/es.json').read_text(encoding='utf-8')))
en=flatten(json.loads((root/'data/lang/en.json').read_text(encoding='utf-8')))
assert es.keys()==en.keys(),es.keys()^en.keys()
for path in list((root/'src').rglob('*.py'))+[root/'tools/export_content.py']:
 source=path.read_text(encoding='utf-8-sig');ast.parse(source,filename=str(path))
 for key in re.findall(r'\.text\([\"\'](ui\.[\w.]+)[\"\']',source):assert key in es,(path,key)
for item in json.loads((root/'data/game/items.json').read_text(encoding='utf-8')):
 if item.get('enabled'):
  for field in ('name','short','detail'):assert item['text_key']+'.'+field in es,(item['id'],field)
print(f'Syntax and translation references OK; {len(es)} matching translation keys in both languages.')
