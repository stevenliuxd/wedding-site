import csv
import io
import os
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import (
    Flask, Response, abort, g, redirect, render_template, request, url_for,
)

MOUNTAIN_TZ = ZoneInfo('America/Edmonton')

BASE_DIR = Path(__file__).parent
DB_PATH = Path(os.environ.get('RSVP_DB', BASE_DIR / 'rsvps.db'))
SCHEMA_PATH = BASE_DIR / 'schema.sql'

ADMIN_USER = os.environ.get('ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')

ATTENDING_VALUES = {'yes', 'no'}
STARTER_CHOICES = {
    'Canadian Lobster Bisque, Saffron Cream, Brioche Croutons',
    'Roasted Beets & Apple Salad, Honey Goat Cheese, Candied Pecans, Balsamic Dressing',
}
MAIN_CHOICES = {
    'Pan Seared Marinated Chicken Supreme, Duck fat Smashed Potatoes, Asparagus, Chimichurri Sauce',
    'Slow Roasted Alberta Beef Striploin, Confit Baby Potatoes, Black Garlic Haricots Verts, Red wine Sauce',
}
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.template_filter('mountain_time')
def mountain_time(utc_str):
    if not utc_str:
        return ''
    dt = datetime.fromisoformat(utc_str).replace(tzinfo=timezone.utc)
    return dt.astimezone(MOUNTAIN_TZ).strftime('%Y-%m-%d %H:%M %Z')


def get_db():
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript(SCHEMA_PATH.read_text())


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/rehearsal')
def rehearsal():
    return render_template('rehearsal.html')


@app.route('/weddingparty')
def wedding_party():
    return render_template('wedding_party.html')


@app.route('/drinks')
def drinks():
    return render_template('drinks.html')


def parse_guests(form):
    # Form fields look like: guests[0][full_name], guests[1][attending], etc.
    pattern = re.compile(r'^guests\[(\d+)\]\[([a-z_]+)\]$')
    by_index = {}
    for key, value in form.items():
        m = pattern.match(key)
        if not m:
            continue
        idx = int(m.group(1))
        field = m.group(2)
        by_index.setdefault(idx, {})[field] = value.strip()
    return [by_index[i] for i in sorted(by_index)]


@app.route('/rsvp', methods=['GET', 'POST'])
def rsvp():
    if request.method == 'GET':
        return render_template('rsvp.html')

    message = request.form.get('message', '').strip() or None

    guests = parse_guests(request.form)
    if not guests:
        return render_template('rsvp.html', error='Please add at least one guest.'), 400

    cleaned = []
    for i, g_data in enumerate(guests, start=1):
        name = g_data.get('full_name', '')
        attending = g_data.get('attending', '')
        if not name:
            return render_template('rsvp.html', error=f'Guest {i}: name is required.'), 400
        if attending not in ATTENDING_VALUES:
            return render_template('rsvp.html', error=f'Guest {i}: please select attending or not.'), 400
        starter = g_data.get('starter') or None
        main = g_data.get('main_course') or None
        dietary = g_data.get('dietary') or None
        if attending == 'yes':
            if not starter or starter not in STARTER_CHOICES:
                return render_template('rsvp.html', error=f'Guest {i}: please choose a starter.'), 400
            if not main or main not in MAIN_CHOICES:
                return render_template('rsvp.html', error=f'Guest {i}: please choose a main course.'), 400
        else:
            starter = main = dietary = None
        cleaned.append({
            'full_name': name,
            'attending': attending,
            'starter': starter,
            'main_course': main,
            'dietary': dietary,
        })

    db = get_db()
    cur = db.execute(
        'INSERT INTO rsvps (message, ip, user_agent) VALUES (?, ?, ?)',
        (message, request.remote_addr, request.headers.get('User-Agent', '')[:500]),
    )
    rsvp_id = cur.lastrowid
    db.executemany(
        'INSERT INTO guests (rsvp_id, full_name, attending, starter, main_course, dietary) '
        'VALUES (?, ?, ?, ?, ?, ?)',
        [(rsvp_id, g['full_name'], g['attending'], g['starter'], g['main_course'], g['dietary'])
         for g in cleaned],
    )
    db.commit()
    return redirect(url_for('thanks'))


@app.route('/thanks')
def thanks():
    return render_template('thanks.html')


def require_admin(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not ADMIN_PASSWORD:
            abort(503, 'ADMIN_PASSWORD not configured')
        auth = request.authorization
        if not auth or not (
            secrets.compare_digest(auth.username or '', ADMIN_USER)
            and secrets.compare_digest(auth.password or '', ADMIN_PASSWORD)
        ):
            return Response(
                'Authentication required.', 401,
                {'WWW-Authenticate': 'Basic realm="RSVP Admin"'},
            )
        return view(*args, **kwargs)
    return wrapped


@app.route('/admin')
@require_admin
def admin():
    db = get_db()
    rows = db.execute(
        'SELECT r.id AS rsvp_id, r.submitted_at, r.message, '
        '       g.full_name, g.attending, g.starter, g.main_course, g.dietary '
        'FROM rsvps r JOIN guests g ON g.rsvp_id = r.id '
        'ORDER BY r.submitted_at DESC, r.id DESC, g.id ASC'
    ).fetchall()
    rsvp_counts = {}
    for row in rows:
        rsvp_counts[row['rsvp_id']] = rsvp_counts.get(row['rsvp_id'], 0) + 1
    multi_guest_rsvp_ids = {rid for rid, count in rsvp_counts.items() if count > 1}
    stats = {
        'attending': db.execute("SELECT COUNT(*) FROM guests WHERE attending='yes'").fetchone()[0],
        'declined': db.execute("SELECT COUNT(*) FROM guests WHERE attending='no'").fetchone()[0],
        'soup': db.execute("SELECT COUNT(*) FROM guests WHERE starter LIKE 'Canadian Lobster Bisque%'").fetchone()[0],
        'salad': db.execute("SELECT COUNT(*) FROM guests WHERE starter LIKE 'Roasted Beets%'").fetchone()[0],
        'chicken': db.execute("SELECT COUNT(*) FROM guests WHERE main_course LIKE 'Pan Seared%'").fetchone()[0],
        'beef': db.execute("SELECT COUNT(*) FROM guests WHERE main_course LIKE 'Slow Roasted%'").fetchone()[0],
    }
    return render_template('admin.html', rows=rows, stats=stats,
                           multi_guest_rsvp_ids=multi_guest_rsvp_ids,
                           rsvp_counts=rsvp_counts)


@app.route('/admin/rsvps/<int:rsvp_id>/delete', methods=['POST'])
@require_admin
def admin_delete_rsvp(rsvp_id):
    db = get_db()
    db.execute('DELETE FROM rsvps WHERE id = ?', (rsvp_id,))
    db.commit()
    return redirect(url_for('admin'))


@app.route('/admin/export.csv')
@require_admin
def admin_export():
    db = get_db()
    rows = db.execute(
        'SELECT r.submitted_at, r.message, '
        '       g.full_name, g.attending, g.starter, g.main_course, g.dietary '
        'FROM rsvps r JOIN guests g ON g.rsvp_id = r.id '
        'ORDER BY r.submitted_at DESC, g.id ASC'
    ).fetchall()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['submitted_at', 'guest_name', 'attending',
                     'starter', 'main_course', 'dietary', 'message'])
    for r in rows:
        writer.writerow([r['submitted_at'], r['full_name'], r['attending'],
                         r['starter'] or '', r['main_course'] or '', r['dietary'] or '',
                         r['message'] or ''])
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename="rsvps.csv"'},
    )


if __name__ == '__main__':
    if not DB_PATH.exists():
        init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
