import os, sqlite3, sys, time, urllib.request

DB = os.environ.get('DB_PATH', '/data/energia.db')

def web():
    urllib.request.urlopen('http://127.0.0.1:5000/health', timeout=2)

def coletor():
    con = sqlite3.connect(DB, timeout=2)
    ts = con.execute('SELECT MAX(ts) FROM amostras').fetchone()[0]
    if ts is None or time.time() - ts > 5:
	raise RuntimeError('sem amostra recente')

try:
    {'web': web, 'coletor': coletor}[sys.argv[1]]()
except Exception:
    sys.exit(1)
