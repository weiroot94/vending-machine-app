# Vending App

Daemon-style kiosk application that powers a network-connected vending machine. The project serves a responsive product catalogue, talks to payment peripherals (coin & bill acceptors), exchanges data with a remote vending backend, and drives a browser-based UI that can run in kiosk mode on the machine.

## Features
- Touch-friendly product catalogue with category navigation, multi-language copy, and theming.
- QR-code based checkout flow backed by JWTs plus remote order confirmation endpoints.
- Hardware integrations for coin/note acceptors (ccTalk) and product motors via PCA9685.
- Background updater that syncs ads, products, language packs, and firmware packages from the central API.
- Live status updates and motor commands delivered over Flask-SocketIO.

## Architecture Snapshot
- `main.py` boots the Flask web server, Socket.IO, DB connection pool, and auto-update thread.
- `src/` holds domain logic: API facades, controllers, hardware drivers, and database helpers.
- `templates/` and `static/` provide the HTML/CSS/JS kiosk front end.
- `service_starter.sh` and `service_remove.sh` help deploy the app as a systemd service.
- SQLite lives in `db/vm.db`; tables are created on first boot and hydrated by the updater.

## Prerequisites
- Python 3.10+ and `pip`.
- A Chromium-based browser available on the target device (for kiosk mode).
- For hardware features: Raspberry Pi/PC with ccTalk-compatible cash acceptors and Adafruit PCA9685.

### Linux system libraries (Ubuntu 22.04)

```bash
sudo apt-get install build-essential libgl1-mesa-dev python3-dev python3-pyqt5
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
sudo apt install libcairo2-dev libxt-dev libgirepository1.0-dev
```

### Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install pycairo PyGObject  # required for pywebview on Linux
```

> On Windows, activate the virtual environment with `.venv\Scripts\activate` and skip the `pycairo`/`PyGObject` step unless you are running via WSL.

## Configuration
Create a `.env` file in the project root and set values that match your deployment:

| Variable | Required | Description |
| --- | --- | --- |
| `DEBUG` | optional (default `false`) | Enables verbose logging and skips hardware initialization. Use `true` for local development or Windows simulation. |
| `FULLSCREEN` | optional (default `false`) | Adds `--kiosk` when launching Chromium so the UI fills the screen. |
| `WEB_API_SERVER` | **yes** | Base URL of the vending cloud API (exposes `/client/ping`, `/client/sell`, etc.). |
| `SERIALNO` | **yes** | Unique identifier for the vending machine; used for API calls and telemetry. |
| `QRSECRET` | **yes** | Secret used by Flask-JWT-Extended to sign QR payload tokens. Keep this private. |
| `SOCKET_SERVER` | optional | External Socket.IO endpoint that mirrors machine events for the mobile/web client. |

Example `.env`:

```bash
DEBUG=true
FULLSCREEN=false
WEB_API_SERVER=https://api.example.com
SERIALNO=VM-DEV-0001
QRSECRET=super-secret-key
SOCKET_SERVER=https://socket.example.com
```

## Running the app
- Activate your virtual environment.
- Ensure `.env` is populated with valid values and that the remote API is reachable (or mock the endpoints for development).
- Start the Flask + Socket.IO server:

```bash
python main.py
```

- In production on Linux, the app automatically launches Chromium in kiosk mode. During local development (especially on Windows) set `DEBUG=true` and manually open `http://localhost:5000` in your browser.

### Background update cycle
`DatabaseUpdater` runs in its own thread and hits the `/client/ping` endpoint every 10 seconds. Depending on the response payload it can:
- download & apply code bundles,
- refresh product/language/info tables inside `db/vm.db`,
- fetch the latest advertising video, and
- toggle a flag consumed by the UI to prompt reloads.

If your environment does not expose the remote API, stub these endpoints or disable the thread during development.

## Deploying as a service (Linux)
`service_starter.sh` provisions a systemd unit that keeps the app alive and logs to `app.log` in the project root.

```bash
chmod +x service_starter.sh service_remove.sh
./service_starter.sh
```

To remove the service:

```bash
./service_remove.sh
```

## Packaging
- Use PyInstaller to create a distributable bundle (update `app.spec` or call PyInstaller directly with `main.py`).
- The generated binary should be placed alongside `templates/` and `static/` assets to keep resource paths intact.

## Development tips
- Use `DEBUG=true` and comment out hardware-specific imports when running without the peripherals.
- The SQLite database is created on demand; remove the `db/` directory to reset local data.
- Socket.IO handlers live in `src/route/route.py`; mock messages to simulate AI/motor flows.

## License
This project is released under the MIT License. See `LICENSE` for details.
