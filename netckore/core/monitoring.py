"""Network monitoring and diagnosis logic for Netckore.

The diagnosis flow is designed for people without technical skills:
each category is measured independently, results are human-readable and
suggestions are provided for every failure state.
"""
import platform
import socket
import subprocess
import time
import json
import os
from datetime import datetime

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
PING_TARGETS = ["1.1.1.1", "8.8.8.8"]   # IPs públicas confiables
DNS_DOMAIN = "cloudflare.com"           # Dominio usado para probar DNS
MIN_VALID_PING = 20.0                   # Ping bajo = excelente
MAX_VALID_PING = 300.0                  # Ping alto pero usable

CATEGORY_ORDER = [
    "connectivity",
    "ping",
    "dns",
    "router",
    "wifi",           # NUEVO: diagnóstico WiFi/LAN
    "gateway_fix",    # NUEVO: sugerencias automáticas de reparación
]


# ------------------------------------------------------------------
# Available categories + defaults
# ------------------------------------------------------------------
def diagnosis_categories():
    """Return the list of available diagnosis categories."""
    return [
        {"id": "connectivity", "label": "Conectividad básica", "description": "Verifica si tienes acceso a internet"},
        {"id": "ping", "label": "Latencia", "description": "Mide el tiempo de respuesta entre tu PC y servidores públicos"},
        {"id": "dns", "label": "DNS", "description": "Verifica que los nombres de dominio se resuelvan correctamente"},
        {"id": "router", "label": "Puerta de enlace", "description": "Comprueba si tu router local está accesible"},
        {"id": "wifi", "label": "Red WiFi / LAN", "description": "Analiza la señal, velocidad y configuración de tu red local"},
        {"id": "gateway_fix", "label": "Reparar conexión", "description": "Sugiere acciones automáticas para restaurar la conexión"},
    ]


def default_categories():
    """Safe default categories for a quick diagnosis."""
    return ["connectivity", "ping", "dns", "router"]


# ------------------------------------------------------------------
# Core diagnostics
# ------------------------------------------------------------------
def diagnose_connectivity(log=None):
    """Check basic connectivity to well-known public IPs."""
    results = {
        "online": False,
        "checks": [],
    }
    for host in PING_TARGETS:
        try:
            start = time.monotonic()
            socket.create_connection((host, 53), timeout=3.0).close()
            elapsed = round((time.monotonic() - start) * 1000, 1)
            ok = elapsed < 500
            if ok and log is not None:
                log("🔌 Conexión: la red está activa", "success")
            elif ok and log is None:
                pass
            else:
                if log is not None:
                    log(f"⚠️ Conexión a {host}: elevada ({elapsed} ms)", "warning")
                if log is None:
                    pass
            results["checks"].append({"host": host, "ok": ok, "ms": elapsed})
            if ok:
                results["online"] = True
                break
        except OSError:
            continue
    return results


def diagnose_ping(log=None):
    """Ping public targets and return average latency in ms, or None."""
    results = {
        "avg": None,
        "samples": [],
    }
    if log is not None:
        log("🏓 Mediendo latencia...", "info")
    if platform.system().lower() == "windows":
        count_arg = "-n"
    else:
        count_arg = "-c"
    latencies = []
    for host in PING_TARGETS[:2]:
        try:
            output = subprocess.run(
                ["ping", count_arg, "1", "-w", str(5000), host],
                capture_output=True, text=True, timeout=8,
            )
            if output.returncode != 0:
                if log is not None:
                    log(f"🏓 Ping a {host}: falló", "error")
                continue
            text = output.stdout.lower()
            for part in text.split("avg"):
                for word in part.split():
                    word = word.strip().split("=")
                    val = word[0]
                    if val and val.replace("/", "").isdigit():
                        latencies.append(float(val))
            if latencies:
                results["samples"].append(round(max(latencies), 1))
        except (subprocess.TimeoutExpired, OSError, ValueError):
            continue
    if latencies:
        results["avg"] = round(sum(latencies) / len(latencies), 1)
    if log is not None:
        if results["avg"] is not None:
            log(f"🏓 Latencia promedio: {results['avg']} ms", "info")
        else:
            log("🏓 No se pudo medir la latencia", "error")
    elif not results["avg"]:
        pass
    return results


def diagnose_dns(log=None):
    """Test DNS resolution of a known domain."""
    domain = DNS_DOMAIN
    try:
        resolved = socket.gethostbyname(domain)
        is_ok = True
    except socket.gaierror:
        resolved = None
        is_ok = False

    msg = {"dns_ok": is_ok, "resolved": resolved}
    if log is not None:
        if is_ok:
            log(f"🌐 DNS: '{domain}' -> {resolved}", "success")
        else:
            log(f"❌ DNS: no se pudo resolver '{domain}'", "error")
    return msg


def diagnose_router(log=None):
    """Identify the local gateway and verify LAN accessibility."""
    gw = _detect_gateway()
    results = {
        "gateway": gw,
        "lan_alive": False,
    }
    if gw:
        if log is not None:
            log(f"🌐 Puerta de enlace local detectada: {gw}", "info")
        results["lan_alive"] = True
        results["message"] = f"🌐 {gw}"
    else:
        if log is not None:
            log("⚠️ No se encontró puerta de enlace local", "warning")
        results["message"] = "⚠️ No se encontró puerta de enlace"
    return results


def diagnose_wifi(log=None):
    """Analyze WiFi/LAN connection details (Windows only)."""
    results = {
        "interface": None,
        "signal": None,
        "ssid": None,
        "band": None,
        "channel": None,
        "ipv4": None,
        "mac": None,
        "speed_mbps": None,
    }

    try:
        if platform.system().lower() != "windows":
            return results

        # Get WiFi info via netsh
        output = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True, timeout=10,
        )
        if output.returncode == 0:
            for line in output.stdout.splitlines():
                line = line.strip()
                if line.startswith("SSID") and ":" in line:
                    results["ssid"] = line.split(":", 1)[1].strip()
                elif "Signal" in line and ":" in line and "Signal" == line.split(":")[0].strip():
                    sig = line.split(":", 1)[1].strip().replace("%", "")
                    if sig.isdigit():
                        results["signal"] = int(sig)
                elif "Radio type" in line or "Tipo de radio" in line:
                    results["band"] = line.split(":", 1)[1].strip()
                elif "Channel" in line or "Canal" in line:
                    ch = line.split(":", 1)[1].strip()
                    if ch.isdigit():
                        results["channel"] = int(ch)
                elif "Physical address" in line or "Dirección física" in line:
                    results["mac"] = line.split(":", 1)[1].strip()
                elif "Receive rate" in line or "Velocidad de recepción" in line:
                    sp = line.split(":", 1)[1].strip().replace("Mbps", "").strip()
                    try:
                        results["speed_mbps"] = int(sp)
                    except ValueError:
                        pass

        # Get IPv4
        output = subprocess.run(
            ["ipconfig"], capture_output=True, text=True, timeout=10,
        )
        if output.returncode == 0:
            lines = output.stdout.splitlines()
            for i, line in enumerate(lines):
                if "IPv4" in line or "IPv4" in line:
                    parts = line.split(":")
                    if len(parts) == 2:
                        results["ipv4"] = parts[1].strip()
                        break

        # Log summary
        if log is not None:
            if results["ssid"]:
                sig = results["signal"]
                sig_str = f" ({sig}%)" if sig else ""
                log(f"📶 WiFi: {results['ssid']}{sig_str}", "info")
            if results["ipv4"]:
                log(f"📍 IP local: {results['ipv4']}", "info")
            if results["speed_mbps"]:
                log(f"⚡ Velocidad de enlace: {results['speed_mbps']} Mbps", "info")

    except (subprocess.TimeoutExpired, OSError):
        pass

    return results


def diagnose_gateway_fix(results, log=None):
    """Generate troubleshooting suggestions based on diagnosis results.

    Returns a dict with:
    - actions: list of dicts {title, description, command?, type}
    - critical: bool (whether connection is completely down)
    """
    suggestions = {
        "actions": [],
        "critical": False,
    }

    online = results.get("online", False)
    dns_ok = results.get("dns_ok", False)
    gateway_found = results.get("gateway_found", False)
    ping_avg = results.get("ping_avg")

    if not online:
        suggestions["critical"] = True
        suggestions["actions"].extend([
            {
                "title": "Reiniciar el router",
                "description": "Desconecta el router de la corriente, espera 30 segundos y vuelve a conectarlo. Resuelve la mayoría de problemas.",
                "type": "hardware",
                "priority": 1,
            },
            {
                "title": "Verificar cables / WiFi",
                "description": "Asegúrate de que el cable Ethernet está bien conectado o que el WiFi está activado en tu dispositivo.",
                "type": "check",
                "priority": 2,
            },
            {
                "title": "Renovar IP (Windows)",
                "description": "Ejecuta en terminal como administrador: ipconfig /release && ipconfig /renew",
                "type": "command",
                "command": "ipconfig /release && ipconfig /renew",
                "priority": 3,
            },
            {
                "title": "Flush DNS",
                "description": "Limpia la caché DNS local: ipconfig /flushdns",
                "type": "command",
                "command": "ipconfig /flushdns",
                "priority": 4,
            },
        ])
    else:
        # Online but with issues
        if not dns_ok:
            suggestions["actions"].append({
                "title": "Cambiar DNS a Cloudflare/Google",
                "description": "Configura DNS 1.1.1.1 y 8.8.8.8 en tu adaptador de red. Mejora resolución y privacidad.",
                "type": "settings",
                "priority": 1,
            })
        if not gateway_found:
            suggestions["actions"].append({
                "title": "Comprobar conexión al router",
                "description": "Intenta acceder a la interfaz del router (ej. 192.168.1.1 o 192.168.0.1) desde el navegador.",
                "type": "check",
                "priority": 2,
            })
        if ping_avg and ping_avg > MAX_VALID_PING:
            suggestions["actions"].append({
                "title": "Latencia alta detectada",
                "description": "Acércate al router, usa cable Ethernet o reinicia el router. Verifica que no haya descargas pesadas.",
                "type": "wifi",
                "priority": 3,
            })

    if log is not None:
        for action in suggestions["actions"]:
            log(f"🔧 {action['title']}: {action['description']}", "info")

    return suggestions


def _detect_gateway():
    """Detect the default gateway IP."""
    try:
        if platform.system().lower() == "windows":
            output = subprocess.run(["ipconfig"], capture_output=True, text=True, timeout=10)
            for line in output.stdout.splitlines():
                low = line.lower()
                if "puerta de enlace predeterminada" in low or "default gateway" in low:
                    parts = line.split(":")
                    if len(parts) == 2:
                        val = parts[1].strip()
                        if val:
                            return val
            return None
        else:
            output = subprocess.run(["ip", "route", "get", "1.1.1.1"],
                                     capture_output=True, text=True, timeout=10)
            tokens = output.stdout.split()
            for i, tok in enumerate(tokens):
                if tok == "via" and i + 1 < len(tokens):
                    return tokens[i + 1]
    except (subprocess.TimeoutExpired, OSError):
        return None
    return None


# ------------------------------------------------------------------
# Helper: classify ping result
# ------------------------------------------------------------------
def classify_ping(avg):
    """Classify ping latency into quality levels."""
    if avg is None:
        return {"level": "none", "label": "N/A", "color": "#9ca3af"}
    if avg < MIN_VALID_PING:
        return {"level": "good", "label": "Excelente", "color": "#4ade80"}
    if avg <= MAX_VALID_PING:
        return {"level": "fair", "label": "Bastante bien", "color": "#fbbf24"}
    return {"level": "bad", "label": "Alto", "color": "#f87171"}


# ------------------------------------------------------------------
# Master run
# ------------------------------------------------------------------
def run_diagnosis(selected, log=None):
    """Run the selected diagnosis steps and return consolidated results."""
    results = {
        "steps": [],          # [(kind, message)] per step
        "online": False,
        "ping_avg": None,
        "dns_ok": False,
        "gateway": None,
        "gateway_found": False,
        "wifi": {},
        "fix_suggestions": {},
        "summary": None,
    }

    for category in selected:
        if category == "connectivity":
            r = diagnose_connectivity(log)
            results["online"] = r["online"]
            results["steps"].append({
                "kind": "success" if r["online"] else "error",
                "message": _("connection_online") if r["online"] else _("connection_offline"),
            })
        elif category == "ping":
            r = diagnose_ping(log)
            results["ping_avg"] = r["avg"]
            cls = classify_ping(r["avg"])
            if r["avg"] is not None:
                results["steps"].append({
                    "kind": cls["color"] if cls["level"] == "good" else ("warning" if cls["level"] == "bad" else "info"),
                    "message": _("ping_result").format(ping=round(r["avg"], 1)),
                })
            else:
                results["steps"].append({"kind": "error", "message": _("ping_failed")})
        elif category == "dns":
            r = diagnose_dns(log)
            results["dns_ok"] = r["dns_ok"]
            results["steps"].append({
                "kind": "success" if r["dns_ok"] else "error",
                "message": _("dns_ok") if r["dns_ok"] else _("dns_failed"),
            })
        elif category == "router":
            r = diagnose_router(log)
            results["gateway"] = r["gateway"]
            results["gateway_found"] = r["lan_alive"]
            results["steps"].append({
                "kind": "info" if r["lan_alive"] else "warning",
                "message": r["message"],
            })
        elif category == "wifi":
            r = diagnose_wifi(log)
            results["wifi"] = r
            wifi_msg = []
            if r.get("ssid"):
                wifi_msg.append(f"📶 {r['ssid']}")
            if r.get("signal") is not None:
                wifi_msg.append(f"{r['signal']}%")
            if r.get("speed_mbps"):
                wifi_msg.append(f"{r['speed_mbps']} Mbps")
            msg = " | ".join(wifi_msg) if wifi_msg else "Sin info WiFi"
            results["steps"].append({"kind": "info", "message": msg})
        elif category == "gateway_fix":
            r = diagnose_gateway_fix(results, log)
            results["fix_suggestions"] = r
            for action in r.get("actions", [])[:3]:
                results["steps"].append({
                    "kind": "info",
                    "message": f"💡 {action['title']}: {action['description'][:60]}...",
                })

    # Build human-readable summary
    results["summary"] = _build_summary(results)
    return results


def _build_summary(results):
    """Generate a user-friendly one-line summary from diagnosis results."""
    online_status = results["online"]
    latency = results["ping_avg"]

    parts = [
        "🌐 Conexión: " + ("✅ ACTIVA" if online_status else "❌ NO DETECTADA"),
    ]
    if online_status and latency is not None:
        parts.append(f"🏓 Latencia: {round(latency)} ms")
    if not results["dns_ok"]:
        parts.append("🌐 DNS: ⚠️")
    if not results["gateway_found"]:
        parts.append("🌐 Gateway: ⚠️")

    extra = []
    if results["steps"]:
        extra.append("📋 Ver detalles en resultados")

    return "; ".join(parts) + (" ... " + "; ".join(extra) if extra else "")


# ------------------------------------------------------------------
# Live stats for pusher
# ------------------------------------------------------------------
def collect_network_stats():
    """Return current network stats for the live dashboard."""
    return {
        "online": _is_online(),
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }


def _is_online(timeout=3.0):
    """Quick connectivity check: try to connect to a well-known host."""
    for host in PING_TARGETS:
        try:
            socket.create_connection((host, 53), timeout=timeout).close()
            return True
        except OSError:
            continue
    return False