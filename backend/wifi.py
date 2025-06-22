import subprocess
from typing import List

SSID = "QuizFix"
AP_SERVICE = "quizwifi"


def _run(cmd: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)


def start_ap() -> bool:
    result = _run(["sudo", "systemctl", "start", f"{AP_SERVICE}.service"])
    return result.returncode == 0


def stop_ap() -> bool:
    result = _run(["sudo", "systemctl", "stop", f"{AP_SERVICE}.service"])
    return result.returncode == 0


def status_ap() -> dict:
    status_cp = _run(["systemctl", "is-active", f"{AP_SERVICE}.service"])
    is_active = status_cp.stdout.strip() == "active"

    clients: List[str] = []
    if is_active:
        iw = _run(["sudo", "iw", "dev", "wlan0", "station", "dump"])
        for line in iw.stdout.splitlines():
            if line.startswith("Station "):
                mac = line.split()[1]
                clients.append(mac)

    return {"active": is_active, "clients": clients, "ssid": SSID} 