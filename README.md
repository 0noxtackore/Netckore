# Netckore

> «La tecnología conecta al mundo. Netckore ayuda a que esa conexión no se convierta en una barrera». 🌍

**Netckore** es una herramienta de diagnóstico y reparación de conexión a internet construida con la misma simplicidad y elegancia tecnológica de **Fluxckore** (0noxtackore). Una sola edición, sin versiones PRO ni Beta, sin dependencias pesadas.

---

## Características

- 🔍 **Diagnóstico de conexión** — verifica conectividad básica, DNS, latencia y puerta de enlace
- 🌐 **Interfaz autónoma** — HTML/CSS/JS renderizado por WebView2, sin toolkits pesados
- 🧠 **Accesible para todos** — diseñado para personas sin conocimientos técnicos
- 🌍 **104 idiomas** — detección automática del idioma del sistema (español por defecto)
- 🪟 **Windows 10/11 (x64)**

---

## Requisitos

- Windows 10/11 (x64)
- Microsoft Edge WebView2 Runtime (preinstalado en la mayoría de sistemas)
- Python 3.10+ (solo para ejecutar desde código fuente)

---

## Uso

### Desde el código fuente

```powershell
git clone https://github.com/0noxtackore/netckore.git netckore
cd netckore
pip install -r requirements.txt
python -m netckore
```

### Lanzador rápido

```powershell
# Doble clic en run.bat
```

---

## Estructura del proyecto

```text
netckore/
├── netckore/                 # Paquete de aplicación
│   ├── app.py              # Backend (pywebview) y orquestación
│   ├── i18n.py             # Gestor de traducciones
│   ├── core/               # Lógica de diagnóstico
│   │   ├── monitoring.py    # Diagnóstico de red
│   │   ├── system.py        # Utilidades del sistema
│   │   ├── sounds.py        # Sonidos nativos (MCI)
│   │   ├── startup_log.py   # Logs de inicio
│   │   ├── browser_profile.py # Perfil WebView2
│   │   ├── headless.py      # Proceso elevado
│   │   └── single_instance.py # Una sola instancia
│   └── frontend/           # Interfaz HTML/CSS/JS
├── locales/                # Traducciones (JSON)
├── assets/                 # Recursos visuales
├── packaging/              # PyInstaller spec, versión
├── requirements.txt        # Dependencias
└── run.bat / run.sh        # Lanzadores
```

---

## Construcción

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller packaging/netckore.spec --noconfirm
```

Resultado: `dist/Netckore/Netckore.exe`

---

## Licencia

Copyright (c) 2026 Netckore Team — 0noxtackore.
