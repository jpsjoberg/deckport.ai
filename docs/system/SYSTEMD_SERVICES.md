## Deckport.ai Services (systemd) – New Structure

This guide documents how to manage the Deckport.ai services with the new modular structure. Services are organized in the `services/` directory with shared code in `shared/`.

### Service Overview

**System Services (Production)**:
- ✅ `api.service` – REST API service (port 8002)
  - Location: `services/api/`
  - Status: Working with new structure
- ⚠️ `frontend.service` – Web frontend service (port 8001)  
  - Location: `services/frontend/`
  - Status: Needs configuration update
- 📋 `realtime.service` – WebSocket service (Phase 2)
- 📋 `console-bridge.service` – Console communication (Phase 3)

**Development Services**:
- 🔧 `scripts/dev-start.sh` – Development frontend (port 5000)
  - Checks API availability
  - Starts frontend with proper environment
  - Shows new structure information

### Current Status
- ✅ **API Service**: Working with new structure on port 8002
- ⚠️ **Frontend Service**: Needs systemd config update for new structure
- ✅ **Database**: PostgreSQL connected with sample data
- ✅ **Development**: `dev-start.sh` script working

### Inspect units

- System-wide units:
```bash
systemctl status api
systemctl status frontend
```

- User-level unit (jp):
```bash
systemctl --user status deckport-frontend
```

### Start/stop/restart

- System-wide:
```bash
sudo systemctl start api
sudo systemctl restart api
sudo systemctl stop api

sudo systemctl start frontend
sudo systemctl restart frontend
sudo systemctl stop frontend
```

- User-level:
```bash
systemctl --user start deckport-frontend
systemctl --user restart deckport-frontend
systemctl --user stop deckport-frontend
```

### Enable on boot

- System-wide:
```bash
sudo systemctl enable api frontend
```

- User-level (jp):
```bash
systemctl --user enable deckport-frontend
loginctl enable-linger jp  # keep user services across reboots
```

### Logs

- System-wide:
```bash
sudo journalctl -u api -f
sudo journalctl -u frontend -f
```

- User-level:
```bash
journalctl --user -u deckport-frontend -f
```

### Editing environment (API_BASE, etc.)

- System-wide units typically live in `/etc/systemd/system/` (e.g., `frontend.service`). Edit and reload:
```bash
sudo nano /etc/systemd/system/frontend.service
sudo systemctl daemon-reload
sudo systemctl restart frontend
```

- User-level unit is at `~/.config/systemd/user/deckport-frontend.service`. Edit and reload:
```bash
nano ~/.config/systemd/user/deckport-frontend.service
systemctl --user daemon-reload
systemctl --user restart deckport-frontend
```

### Current user unit content (reference)

```ini
[Unit]
Description=Deckport Frontend (user)
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/jp/deckport.ai/frontend
Environment=API_BASE=https://api.deckport.ai
ExecStart=/usr/bin/python3 /home/jp/deckport.ai/frontend/app.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
```

### Health checks

- API health (replace with domain if behind NGINX):
```bash
curl -s https://api.deckport.ai/health
```

- Frontend health:
```bash
curl -s http://127.0.0.1:5000/ | head -n1
```

### Tips

- Prefer systemd for auto-restarts and boot-time start
- For development, use the user-level service or run directly with `python`
- Keep environment (API_BASE, keys) in the unit via `Environment=` or an `EnvironmentFile=`

