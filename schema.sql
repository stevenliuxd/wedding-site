CREATE TABLE IF NOT EXISTS rsvps (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    submitted_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    primary_email   TEXT    NOT NULL,
    message         TEXT,
    ip              TEXT,
    user_agent      TEXT
);

CREATE TABLE IF NOT EXISTS guests (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    rsvp_id         INTEGER NOT NULL REFERENCES rsvps(id) ON DELETE CASCADE,
    full_name       TEXT    NOT NULL,
    attending       TEXT    NOT NULL CHECK (attending IN ('yes','no')),
    starter         TEXT,
    main_course     TEXT,
    dietary         TEXT
);

CREATE INDEX IF NOT EXISTS idx_guests_rsvp ON guests(rsvp_id);
