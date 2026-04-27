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
sudo apt install -y python3-venv python3-pip caddy
```

### 2. Put the code somewhere stable

The live deployment lives at `/home/steven/code/wedding-site`. Adjust the paths below if you put it elsewhere.

```bash
mkdir -p ~/code
git clone <repo-url> ~/code/wedding-site
```

### 3. Create venv and initialize the DB

```bash
cd ~/code/wedding-site
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -c "from app import init_db; init_db()"
```

This creates `rsvps.db` next to `app.py`.

### 4. Run as a systemd service

Create `/etc/systemd/system/wedding.service`:

```ini
[Unit]
Description=Dylan & Steven wedding site
After=network.target

[Service]
User=steven
Group=steven
WorkingDirectory=/home/steven/code/wedding-site
Environment="ADMIN_USER=admin"
Environment="ADMIN_PASSWORD=REPLACE_WITH_LONG_RANDOM_STRING"
Environment="RSVP_DB=/home/steven/code/wedding-site/rsvps.db"
ExecStart=/home/steven/code/wedding-site/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now wedding
sudo systemctl status wedding
```

The service runs as `steven` so the gunicorn process can read/write the DB without extra ownership changes.

### 5. Reverse proxy with Caddy + HTTPS

Caddy handles TLS automatically (Let's Encrypt). Edit `/etc/caddy/Caddyfile`:

```
dylanandsteven.ca, www.dylanandsteven.ca {
    reverse_proxy 127.0.0.1:5000
}

dylanandsteven.ddns.net {
    reverse_proxy 127.0.0.1:5000
}
```

```bash
sudo systemctl reload caddy
```

Each hostname listed in the Caddyfile needs to resolve to this server before Caddy can issue a certificate for it.

## Admin

Visit `/admin` and authenticate with `ADMIN_USER` / `ADMIN_PASSWORD` from the systemd unit. Use **Download CSV** to export responses for your seating chart.

## Backups

The whole database is one file. Quick cron backup:

```bash
0 3 * * * cp /home/steven/code/wedding-site/rsvps.db /home/steven/code/wedding-site/backups/rsvps-$(date +\%F).db
```

## Tweaking content

- **Wedding info / copy** → `templates/index.html`
- **Photos** → `static/images/img1.jpg` … `img7.jpg` (swap files in place to update)
- **Menu options** → `templates/rsvp.html` *and* the `STARTER_CHOICES` / `MAIN_CHOICES` sets in `app.py` (the server validates against these)
- **Date / time of countdown** → `static/script.js` (the `target` constant)
- **RSVP deadline text** → `templates/index.html` and `templates/rsvp.html`
