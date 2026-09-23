import json, urllib.request
from concurrent.futures import ThreadPoolExecutor
urls=json.load(urllib.request.urlopen('https://openrpg.de/srd/5e/de/api/spell'))['result']['objects']
def fetch(u):
 try:
  x=json.load(urllib.request.urlopen(u+'/json'))
  return {'name':x['name'],'level':int(x['level']),'school':x['school'],'classes':'','time':x['time'],'range':x['range'],'components':x['components'],'duration':x['duration'],'effect':x['description']['text']}
 except Exception: return None
with ThreadPoolExecutor(max_workers=16) as pool:
 out=[x for x in pool.map(fetch,urls) if x]
json.dump(out,open('assets/srd/spells-2014-de.json','w',encoding='utf-8'),ensure_ascii=False)
print(len(out))
