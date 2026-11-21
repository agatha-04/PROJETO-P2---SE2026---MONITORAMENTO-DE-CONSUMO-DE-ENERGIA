import math, os, sqlite3, threading, time
from flask import Flask, jsonify, render_template, request

DB = os.environ.get('DB_PATH', '/data/energia.db')
TARIFA = float(os.environ.get('TARIFA_RS_KWH', '1.00'))
PWM_DIR = os.environ.get('PWM_DIR', '/pwm')                 # pwm0 montado do host
SERVO_MIN_US = int(os.environ.get('SERVO_MIN_US', '600'))   # pulso para 0 grau
SERVO_MAX_US = int(os.environ.get('SERVO_MAX_US', '2400'))  # pulso para 180 graus
ANGULO_INICIAL = 90
app = Flask(__name__)

# ---------- Servo (PWM por hardware, via sysfs) ----------
pwm_lock = threading.Lock()      # serializa escritas no PWM
servo_lock = threading.Lock()    # protege o dicionario de estado
servo = {'angulo': None, 'ok': False}
varredura = threading.Event()


def _escrever(angulo):
    us = SERVO_MIN_US + (SERVO_MAX_US - SERVO_MIN_US) * angulo / 180.0
    with open(PWM_DIR + '/duty_cycle', 'w') as f:
        f.write(str(int(us * 1000)))          # o sysfs usa nanossegundos
    with servo_lock:
        servo['angulo'], servo['ok'] = round(angulo), True


def mover_servo(angulo):
    angulo = float(angulo)
    if not math.isfinite(angulo):
        raise ValueError('angulo invalido')
    angulo = max(0.0, min(180.0, angulo))
    with pwm_lock:
        _escrever(angulo)


def varredor():
    ang, passo = 0, 10
    while True:
        varredura.wait()
        try:
            with pwm_lock:
                if not varredura.is_set():
                    continue
                _escrever(ang)
        except OSError:
            with servo_lock:
                servo['ok'] = False
            time.sleep(1)
            continue
        ang += passo
        if ang >= 180 or ang <= 0:
            ang = max(0, min(180, ang))
            passo = -passo
        time.sleep(0.15)


def iniciar_servo():
    try:
        mover_servo(ANGULO_INICIAL)
    except OSError:
        pass                                   # sem PWM (ex.: teste no PC): a web continua
    threading.Thread(target=varredor, daemon=True).start()


# ---------- Banco ----------
def consulta(sql, args=()):
    con = sqlite3.connect(DB, timeout=5)
    con.row_factory = sqlite3.Row
    try:
        return con.execute(sql, args).fetchall()
    finally:
        con.close()


@app.get('/health')
def health():
    try:
        ts = consulta('SELECT MAX(ts) AS ts FROM amostras')[0]['ts']
        if ts is not None and time.time() - ts <= 5:
            return jsonify(status='ok'), 200
        return jsonify(status='sem amostra recente'), 503
    except Exception as e:
        return jsonify(status='erro', detalhe=str(e)), 503


@app.get('/api/atual')
def atual():
    r = consulta('SELECT * FROM amostras ORDER BY ts DESC LIMIT 1')
    if not r:
        return jsonify(ok=False), 503
    a = r[0]
    return jsonify(ok=True, ts=a['ts'], tensao_v=a['v_mv'] / 1000,
                   corrente_a=a['i_ma'] / 1000, potencia_w=a['p_mw'] / 1000)


@app.get('/api/historico')
def historico():
    minutos = min(max(int(request.args.get('minutos', 5)), 1), 120)
    rows = consulta('SELECT ts, v_mv, i_ma, p_mw FROM amostras WHERE ts >= ? ORDER BY ts',
                    (int(time.time()) - minutos * 60,))
    return jsonify([{'ts': r['ts'], 'v_v': r['v_mv'] / 1000,
                     'i_a': r['i_ma'] / 1000, 'p_w': r['p_mw'] / 1000} for r in rows])


@app.get('/api/energia')
def energia():
    mws = consulta('SELECT mws FROM acumulado WHERE id = 1')[0]['mws']
    kwh = mws / 3.6e9
    return jsonify(kwh=round(kwh, 6), custo_rs=round(kwh * TARIFA, 4))


# ---------- API do servo ----------
@app.get('/api/servo')
def servo_estado():
    with servo_lock:
        d = dict(servo)
    d['varredura'] = varredura.is_set()
    return jsonify(d)


@app.post('/api/servo')
def servo_mover():
    dados = request.get_json(silent=True) or {}
    try:
        angulo = float(dados['angulo'])
        if not math.isfinite(angulo):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        return jsonify(ok=False, erro='informe angulo entre 0 e 180'), 400
    varredura.clear()
    try:
        mover_servo(angulo)
    except OSError as e:
        with servo_lock:
            servo['ok'] = False
        return jsonify(ok=False, erro=str(e)), 503
    with servo_lock:
        ang = servo['angulo']
    return jsonify(ok=True, angulo=ang)


@app.post('/api/varredura')
def servo_varredura():
    dados = request.get_json(silent=True) or {}
    if dados.get('ligar', True):
        varredura.set()
    else:
        varredura.clear()
    return jsonify(ok=True, varredura=varredura.is_set())


@app.get('/')
def index():
    return render_template('index.html')


iniciar_servo()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
