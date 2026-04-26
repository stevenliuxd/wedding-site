# Dylan & Steven — Wedding Website

A small Flask + SQLite site for the wedding on **August 8, 2026** at **The Ridge, Okotoks**.

## Layout

```
.
├── app.py               # Flask routes
├── schema.sql           # SQLite tables
├── requirements.txt
├── static/
│   ├── styles.css
│   ├── script.js        # countdown + dynamic guest blocks
│   └── images/          # img1.jpg … img7.jpg
└── templates/
    ├── index.html       # public site
    ├── rsvp.html        # form
    ├── thanks.html      # confirmation
    └── admin.html       # protected response viewer
```

The DB lives at `rsvps.db` next to `app.py` (override with `RSVP_DB`).

## Local development (any machine with Python 3.10+)

```bash
python3 -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt
export ADMIN_PASSWORD='change-me'   # required to view /admin
python app.py
```

Open http://localhost:5000 — the DB initializes itself the first time you run.

## Deploy on Ubuntu 24.04

### 1. Install system packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip nginx
```

### 2. Put the code somewhere stable

```bash
sudo mkdir -p /srv/wedding
sudo chown "$USER":"$USER" /srv/wedding
# copy this directory's contents to /srv/wedding
```

### 3. Create venv and initialize the DB

```bash
cd /srv/wedding
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -c "from app import init_db; init_db()"
```

### 4. Run as a systemd service

Create `/etc/systemd/system/wedding.service`:

```ini
[Unit]
Description=Dylan & Steven wedding site
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/wedding
Environment="ADMIN_USER=admin"
Environment="ADMIN_PASSWORD=REPLACE_WITH_LONG_RANDOM_STRING"
Environment="RSVP_DB=/srv/wedding/rsvps.db"
ExecStart=/srv/wedding/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R www-data:www-data /srv/wedding
sudo systemctl daemon-reload
sudo systemctl enable --now wedding
sudo systemctl status wedding
```

### 5. Reverse proxy with nginx + HTTPS

`/etc/nginx/sites-available/wedding`:

```nginx
server {
    listen 80;
    server_name your-domain.example;

    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/wedding /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Free TLS with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.example
```

If you'd rather skip nginx, **Caddy** does HTTPS automatically:

```
your-domain.example {
    reverse_proxy 127.0.0.1:5000
}
```

## Admin

Visit `/admin` and authenticate with `ADMIN_USER` / `ADMIN_PASSWORD` from the systemd unit. Use **Download CSV** to export responses for your seating chart.

## Backups

The whole database is one file. Quick cron backup:

```bash
0 3 * * * cp /srv/wedding/rsvps.db /srv/wedding/backups/rsvps-$(date +\%F).db
```

## Tweaking content

- **Wedding info / copy** → `templates/index.html`
- **Photos** → `static/images/img1.jpg` … `img7.jpg` (swap files in place to update)
- **Menu options** → `templates/rsvp.html` *and* the `STARTER_CHOICES` / `MAIN_CHOICES` sets in `app.py` (the server validates against these)
- **Date / time of countdown** → `static/script.js` (the `target` constant)
- **RSVP deadline text** → `templates/index.html` and `templates/rsvp.html`
