import csv

f = open('backups/scuole_anagrafe.csv', 'r', encoding='utf-8')
rows = [r for r in csv.DictReader(f) if r['CODICEISTITUTORIFERIMENTO'] == 'GRIS001009']
f.close()

print(f'Found {len(rows)} entries for GRIS001009\n')
for r in rows:
    print(f"{r['CODICESCUOLA']:12} | {r['DENOMINAZIONESCUOLA']:40} | SEDE_DIR={r['INDICAZIONESEDEDIRETTIVO']}")
