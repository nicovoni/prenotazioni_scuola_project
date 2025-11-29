import json
p='backups/scuole_index.json'
with open(p,encoding='utf-8') as f:
    idx=json.load(f)
keys=list(idx.keys())
print('COUNT:', len(keys))
print('SAMPLE:', keys[:20])
