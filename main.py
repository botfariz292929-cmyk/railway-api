from flask import Flask, request, jsonify
from werkzeug.middleware.proxy_fix import ProxyFix
import requests
import os
import threading
import time

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

BASE44 = "https://api.base44.com/api/apps/69dcfe355119b1dc9b087c32/entities"
HEADERS = {
    "api_key": "e2e5ae42e69b4f4bbefca3a956ac4bd5",
    "Content-Type": "application/json"
}

PORT = int(os.environ.get("PORT", 8080))

# ===== KEEP ALIVE =====
def keep_alive():
    time.sleep(30)
    while True:
        try:
            requests.get(f"http://localhost:{PORT}/", timeout=5)
            print("[KEEPALIVE] Ping OK", flush=True)
        except Exception as e:
            print(f"[KEEPALIVE] Error: {e}", flush=True)
        time.sleep(240)

t = threading.Thread(target=keep_alive, daemon=True)
t.start()

@app.route("/")
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/functions/receiveData")
def receive():
    q = request.args
    print(f"[receiveData] RAW QUERY: {dict(q)}", flush=True)

    payload = {
        "pv":       float(q.get("pv", 0)),
        "sp":       float(q.get("sp", 0)),
        "output":   int(q.get("out", 0)),
        "mode":     "PID" if q.get("mode") == "P" else "MANUAL",
        "running":  q.get("run") == "1",
        "alarm_hi": q.get("ah") == "1",
        "alarm_lo": q.get("al") == "1",
        "kp":  float(q.get("kp", 0)),
        "ki":  float(q.get("ki", 0)),
        "kd":  float(q.get("kd", 0)),
        "pmax": int(q.get("pm", 240)),
        "rlim": int(q.get("rl", 25))
    }
    print(f"[receiveData] PAYLOAD TO BASE44: {payload}", flush=True)

    try:
        resp = requests.post(
            f"{BASE44}/SensorData",
            headers=HEADERS,
            json=payload,
            timeout=10
        )
        print(f"[receiveData] BASE44 RESPONSE: {resp.status_code} {resp.text[:200]}", flush=True)
    except Exception as e:
        print(f"[receiveData] BASE44 ERROR: {e}", flush=True)

    return jsonify({"status": "ok"})


@app.route("/functions/getCommand")
def get_cmd():
    print("[getCommand] Polling commands...", flush=True)

    try:
        r = requests.get(
            f"{BASE44}/DeviceCommand",
            headers=HEADERS,
            timeout=10
        )
        data = r.json()
        print(f"[getCommand] COMMANDS FROM BASE44: {data}", flush=True)
    except Exception as e:
        print(f"[getCommand] BASE44 ERROR: {e}", flush=True)
        return jsonify({"cmd_sp": None, "cmd_mode": None, "cmd_pwm": None, "cmd_running": None})

    cmd = next((c for c in data if not c.get("consumed")), {})
    print(f"[getCommand] SELECTED CMD: {cmd}", flush=True)

    if cmd.get("id"):
        try:
            requests.put(
                f"{BASE44}/DeviceCommand/{cmd['id']}",
                headers=HEADERS,
                json={"consumed": True},
                timeout=10
            )
            print(f"[getCommand] Marked cmd {cmd['id']} as consumed", flush=True)
        except Exception as e:
            print(f"[getCommand] Mark consumed ERROR: {e}", flush=True)

    result = {
        "cmd_sp":      cmd.get("cmd_sp"),
        "cmd_mode":    cmd.get("cmd_mode"),
        "cmd_pwm":     cmd.get("cmd_pwm"),
        "cmd_running": cmd.get("cmd_running")
    }
    print(f"[getCommand] RETURNING: {result}", flush=True)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
