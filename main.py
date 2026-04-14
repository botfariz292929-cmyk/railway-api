from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BASE44 = "https://base44.app/api/apps/69dcfe355119b1dc9b087c32/entities"
HEADERS = {
    "api_key": "e2e5ae42e69b4f4bbefca3a956ac4bd5",
    "Content-Type": "application/json"
}

@app.route("/functions/receiveData")
def receive():
    q = request.args
    payload = {
        "pv":      float(q.get("pv", 0)),
        "sp":      float(q.get("sp", 0)),
        "output":  int(q.get("out", 0)),
        "mode":    "PID" if q.get("mode") == "P" else "MANUAL",
        "running": q.get("run") == "1",
        "alarm_hi": q.get("ah") == "1",
        "alarm_lo": q.get("al") == "1",
        "kp":  float(q.get("kp", 0)),
        "ki":  float(q.get("ki", 0)),
        "kd":  float(q.get("kd", 0)),
        "pmax": int(q.get("pm", 240)),
        "rlim": int(q.get("rl", 25))
    }
    requests.post(f"{BASE44}/SensorData", headers=HEADERS, json=payload)
    return "OK"

@app.route("/functions/getCommand")
def get_cmd():
    r = requests.get(f"{BASE44}/DeviceCommand", headers=HEADERS).json()
    cmd = next((c for c in r if not c.get("consumed")), {})
    if cmd.get("id"):
        requests.put(
            f"{BASE44}/DeviceCommand/{cmd["id"]}",
            headers=HEADERS,
            json={"consumed": True}
        )
    return jsonify({
        "cmd_sp":      cmd.get("cmd_sp"),
        "cmd_mode":    cmd.get("cmd_mode"),
        "cmd_pwm":     cmd.get("cmd_pwm"),
        "cmd_running": cmd.get("cmd_running")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
