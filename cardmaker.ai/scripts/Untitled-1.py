cat > frontend/app.py <<'PY'
from flask import Flask
app = Flask(__name__)

@app.get("/")
def home():
    return "Hello from FRONTEND at example.com"

# WSGI entrypoint
if __name__ == "__main__":
    app.run()
PY

# WSGI module (gunicorn looks for "app")
ln -sf frontend/app.py frontend/wsgi.py


cat >api/app.py <<'PY'
from flask import Flask, jsonify
app = Flask(__name__)

@app.get("/health")
def health():
    return jsonify(status="ok")

@app.get("/v1/hello")
def hello():
    return jsonify(message="Hello from API at api.example.com")

# WSGI entrypoint
if __name__ == "__main__":
    app.run()
PY

ln -sf api/app.py api/wsgi.py



sudo -s

cat >/etc/systemd/system/frontend.service <<'UNIT'
[Unit]
Description=Gunicorn FRONTEND
After=network.target

[Service]
User=jp
Group=www-data
WorkingDirectory=/home/jp/deckport.ai/frontend
Environment="PATH=/home/jp/deckport.ai/frontend/venv/bin"
ExecStart=/home/jp/deckport.ai/frontend/venv/bin/gunicorn -w 2 -b 127.0.0.1:8001 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

cat >/etc/systemd/system/api.service <<'UNIT'
[Unit]
Description=Gunicorn API
After=network.target

[Service]
User=jp
Group=www-data
WorkingDirectory=/home/jp/deckport.ai/api
Environment="PATH=/home/jp/deckport.ai/api/venv/bin"
# Increase workers if needed
ExecStart=/home/jp/deckport.ai/api/venv/bin/gunicorn -w 2 -b 127.0.0.1:8002 wsgi:app
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now frontend.service
systemctl enable --now api.service
systemctl status frontend.service --no-pager -l
systemctl status api.service --no-pager -l






cat >/etc/nginx/sites-available/frontend <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name deckport.ai www.deckport.ai;

    # proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # Optional: increase upload size
    client_max_body_size 25m;
}
NGINX

# API at api.example.com
cat >/etc/nginx/sites-available/api <<'NGINX'
server {
    listen 80;
    listen [::]:80;
    server_name api.deckport.ai;

    location / {
        proxy_pass http://127.0.0.1:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    # CORS (if your frontend hits the API from the browser)
    add_header Access-Control-Allow-Origin "https://example.com" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, PATCH, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

    # Handle preflight
    if ($request_method = OPTIONS) {
        return 204;
    }

    client_max_body_size 25m;
}
NGINX

ln -s /etc/nginx/sites-available/frontend /etc/nginx/sites-enabled/frontend
ln -s /etc/nginx/sites-available/api /etc/nginx/sites-enabled/api

nginx -t && systemctl reload nginx

certbot --nginx -d deckport.ai -d www.deckport.ai
certbot --nginx -d api.deckport.ai

# Verify timer is active
systemctl status certbot.timer --no-pager