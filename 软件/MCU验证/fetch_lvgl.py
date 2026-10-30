"""Fetch only pinned source files required for this resource probe; verifies Git blob hashes."""
from pathlib import Path
import argparse,concurrent.futures,hashlib,json,urllib.request
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--dest',default=str(Path.home()/'.cache/balancecar/lvgl-v9.2.2'));a=p.parse_args()
dst=Path(a.dest);lock=json.loads((root/'lvgl.lock.json').read_text(encoding='utf-8'))
def fetch(x):
 path=dst/x['path'];path.parent.mkdir(parents=True,exist_ok=True)
 for attempt in range(3):
  try:
   data=path.read_bytes() if path.exists() else urllib.request.urlopen('https://raw.githubusercontent.com/lvgl/lvgl/'+lock['tag']+'/'+x['path'],timeout=30).read()
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==x['git_blob_sha1'],x['path']
   path.write_bytes(data);return
  except Exception:
   if attempt==2:raise
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:list(pool.map(fetch,lock['files']))
print('Verified',len(lock['files']),'LVGL files at',dst)
