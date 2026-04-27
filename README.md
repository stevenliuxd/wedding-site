# Dylan & Steven — Wedding Website

A small Flask + SQLite website for our lovely wedding.

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

## Deployment

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

`scripts/backup-db.sh` runs nightly via cron and ships a compressed snapshot of `rsvps.db` to the NAS at `/mnt/nas-steven/Backups/wedding_site_bk/`.

The script uses `sqlite3 .backup` (safe to run while the site is serving traffic) into a local tempdir, gzips, then copies the `.gz` to the NAS — going direct to CIFS doesn't work because SMB can't satisfy SQLite's file locking.

Crontab entry:

```
0 2 * * * /home/steven/code/wedding-site/scripts/backup-db.sh >> /home/steven/code/wedding-site/logs/backup-db.log 2>&1
```

- **Output**: `rsvps_YYYYMMDD_HHMMSS.db.gz` on the NAS
- **Retention**: 365 days, older `.gz` files auto-pruned (tweak `RETENTION_DAYS` in the script)
- **Log**: `logs/backup-db.log`
- **Safety**: aborts if the NAS isn't mounted at `/mnt/nas-steven`, so it won't silently write into an empty stub directory

Restore:

```bash
gunzip -c /mnt/nas-steven/Backups/wedding_site_bk/rsvps_YYYYMMDD_HHMMSS.db.gz > rsvps.db
```

Run `sudo systemctl stop wedding` first if the site is live, then start it again after replacing the file.

## Tweaking content

- **Wedding info / copy** → `templates/index.html`
- **Photos** → `static/images/img1.jpg` … `img7.jpg` (swap files in place to update)
- **Menu options** → `templates/rsvp.html` *and* the `STARTER_CHOICES` / `MAIN_CHOICES` sets in `app.py` (the server validates against these)
- **Date / time of countdown** → `static/script.js` (the `target` constant)
- **RSVP deadline text** → `templates/index.html` and `templates/rsvp.html`
