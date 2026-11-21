import glob, math, os, sqlite3, time

DB = os.environ.get('DB_PATH', '/data/energia.db')
HW = os.environ.get('HWMON_GLOB', '/ina/hwmon/hwmon*')
SIMULAR = os.environ.get('SIMULAR') == '1'

SQL_AMOSTRAS = """
CREATE TABLE IF NOT EXISTS amostras(
    ts INTEGER PRIMARY KEY,
    v_mv INTEGER,
    i_ma INTEGER,
    p_mw INTEGER
)
"""
SQL_ACUMULADO = """
CREATE TABLE IF NOT EXISTS acumulado(
    id INTEGER PRIMARY KEY CHECK(id=1),
    mws REAL
)
"""


def achar_hwmon():
    for d in glob.glob(HW):
        if os.path.exists(d + '/in1_input'):
            return d
    return None


def ler(d, nome):
    with open(d + '/' + nome) as f:
        return int(f.read().strip())


def leitura():
    # devolve (tensao_mV, corrente_mA, potencia_mW)
    if SIMULAR:
        t = time.time()
        return (5000,
                400 + int(100 * math.sin(t / 5)),
                2000 + int(500 * math.sin(t / 5)))
    d = achar_hwmon()
    if d is None:
        raise OSError('hwmon do INA219 nao encontrado')
    return (ler(d, 'in1_input'),
            ler(d, 'curr1_input'),
            ler(d, 'power1_input') // 1000)


def abrir_banco():
    con = sqlite3.connect(DB, timeout=5)
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA synchronous=NORMAL')
    con.execute(SQL_AMOSTRAS)
    con.execute(SQL_ACUMULADO)
    con.execute('INSERT OR IGNORE INTO acumulado VALUES(1, 0)')
    con.commit()
    return con


def main():
    con = abrir_banco()
    anterior = time.monotonic()
    n = 0
    while True:
        inicio = time.monotonic()
        try:
            v, i, p = leitura()
        except (OSError, ValueError) as e:
            print('erro de leitura:', e, flush=True)
            time.sleep(1)
            continue
        dt = inicio - anterior
        anterior = inicio
        con.execute('INSERT OR REPLACE INTO amostras VALUES(?,?,?,?)',
                    (int(time.time()), v, i, p))
        con.execute('UPDATE acumulado SET mws = mws + ? WHERE id = 1',
                    (p * dt,))
        n += 1
        if n % 60 == 0:
            limite = int(time.time()) - 7 * 86400
            con.execute('DELETE FROM amostras WHERE ts < ?', (limite,))
        con.commit()
        time.sleep(max(0.0, 1.0 - (time.monotonic() - inicio)))


if __name__ == '__main__':
    main()
