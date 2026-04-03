-- ─────────────────────────────────────────────────────────────────────────────
-- seed.sql — IT Asset Management demo database
-- Domain: Enterprise IT Asset Tracking
-- Run: make seed-db
-- ─────────────────────────────────────────────────────────────────────────────

PRAGMA foreign_keys = ON;

-- ─── Tables ──────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS employees (
    employee_id   INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    department    TEXT    NOT NULL,
    location      TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    manager_id    INTEGER REFERENCES employees(employee_id)
);

CREATE TABLE IF NOT EXISTS assets (
    asset_id      INTEGER PRIMARY KEY,
    name          TEXT    NOT NULL,
    category      TEXT    NOT NULL,  -- Laptop, Monitor, Phone, Server
    status        TEXT    NOT NULL,  -- in_use, available, retired, maintenance
    assigned_to   INTEGER REFERENCES employees(employee_id),
    purchase_date TEXT    NOT NULL,
    cost_usd      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS licenses (
    license_id    INTEGER PRIMARY KEY,
    software_name TEXT    NOT NULL,
    vendor        TEXT    NOT NULL,
    seats_total   INTEGER NOT NULL,
    seats_used    INTEGER NOT NULL,
    expiry_date   TEXT    NOT NULL,
    cost_usd      REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS support_tickets (
    ticket_id     INTEGER PRIMARY KEY,
    asset_id      INTEGER NOT NULL REFERENCES assets(asset_id),
    raised_by     INTEGER NOT NULL REFERENCES employees(employee_id),
    priority      TEXT    NOT NULL,  -- high, medium, low
    status        TEXT    NOT NULL,  -- open, in_progress, resolved
    issue         TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    resolved_at   TEXT
);

-- ─── Employees ───────────────────────────────────────────────────────────────

INSERT INTO employees VALUES (1, 'Rohan Mehta',    'Engineering', 'Mumbai',    'rohan.mehta@corp.com',    NULL);
INSERT INTO employees VALUES (2, 'Priya Sharma',   'Engineering', 'Bangalore', 'priya.sharma@corp.com',   1);
INSERT INTO employees VALUES (3, 'Arjun Nair',     'Engineering', 'Mumbai',    'arjun.nair@corp.com',     1);
INSERT INTO employees VALUES (4, 'Sneha Kulkarni', 'Finance',     'Pune',      'sneha.kulkarni@corp.com', NULL);
INSERT INTO employees VALUES (5, 'Vikram Joshi',   'Finance',     'Mumbai',    'vikram.joshi@corp.com',   4);
INSERT INTO employees VALUES (6, 'Anita Desai',    'Finance',     'Pune',      'anita.desai@corp.com',    4);
INSERT INTO employees VALUES (7, 'Kiran Rao',      'HR',          'Bangalore', 'kiran.rao@corp.com',      NULL);
INSERT INTO employees VALUES (8, 'Meera Pillai',   'HR',          'Mumbai',    'meera.pillai@corp.com',   7);
INSERT INTO employees VALUES (9, 'Suresh Patil',   'HR',          'Pune',      'suresh.patil@corp.com',   7);
INSERT INTO employees VALUES (10,'Dev Bhatia',     'Engineering', 'Bangalore', 'dev.bhatia@corp.com',     1);

-- ─── Assets ──────────────────────────────────────────────────────────────────

INSERT INTO assets VALUES (1,  'MacBook Pro 16"',      'Laptop',  'in_use',      2,    '2023-03-15', 2499.00);
INSERT INTO assets VALUES (2,  'MacBook Pro 16"',      'Laptop',  'in_use',      3,    '2023-03-15', 2499.00);
INSERT INTO assets VALUES (3,  'MacBook Air M2',       'Laptop',  'in_use',      5,    '2023-06-01', 1299.00);
INSERT INTO assets VALUES (4,  'MacBook Air M2',       'Laptop',  'available',   NULL, '2023-06-01', 1299.00);
INSERT INTO assets VALUES (5,  'Dell XPS 15',          'Laptop',  'in_use',      10,   '2022-11-20', 1799.00);
INSERT INTO assets VALUES (6,  'Dell XPS 15',          'Laptop',  'maintenance', NULL, '2022-11-20', 1799.00);
INSERT INTO assets VALUES (7,  'LG UltraWide 34"',     'Monitor', 'in_use',      2,    '2023-01-10',  899.00);
INSERT INTO assets VALUES (8,  'LG UltraWide 34"',     'Monitor', 'in_use',      3,    '2023-01-10',  899.00);
INSERT INTO assets VALUES (9,  'LG UltraWide 34"',     'Monitor', 'available',   NULL, '2023-01-10',  899.00);
INSERT INTO assets VALUES (10, 'iPhone 14 Pro',        'Phone',   'in_use',      4,    '2023-09-20',  999.00);
INSERT INTO assets VALUES (11, 'iPhone 14 Pro',        'Phone',   'in_use',      8,    '2023-09-20',  999.00);
INSERT INTO assets VALUES (12, 'iPhone 14 Pro',        'Phone',   'retired',     NULL, '2021-09-20',  999.00);
INSERT INTO assets VALUES (13, 'Dell PowerEdge R750',  'Server',  'in_use',      1,    '2022-05-01', 8999.00);
INSERT INTO assets VALUES (14, 'Dell PowerEdge R750',  'Server',  'in_use',      1,    '2022-05-01', 8999.00);
INSERT INTO assets VALUES (15, 'Synology NAS DS923+',  'Server',  'available',   NULL, '2023-07-15', 1499.00);

-- ─── Licenses ────────────────────────────────────────────────────────────────

INSERT INTO licenses VALUES (1, 'GitHub Enterprise',  'GitHub',    500, 312, '2025-12-31', 21000.00);
INSERT INTO licenses VALUES (2, 'Jira Software',      'Atlassian', 100,  87, '2024-06-30',  8400.00);
INSERT INTO licenses VALUES (3, 'Slack Business+',    'Slack',     200, 178, '2024-08-15', 15000.00);
INSERT INTO licenses VALUES (4, 'MS Office 365',      'Microsoft', 300, 290, '2024-05-01', 36000.00);
INSERT INTO licenses VALUES (5, 'Zoom Business',      'Zoom',      150,  95, '2025-03-20',  9000.00);
INSERT INTO licenses VALUES (6, 'Figma Organisation', 'Figma',      50,  31, '2024-07-01',  5400.00);
INSERT INTO licenses VALUES (7, 'AWS Enterprise',     'Amazon',     10,   8, '2025-09-30', 48000.00);
INSERT INTO licenses VALUES (8, 'Datadog Pro',        'Datadog',    25,  19, '2024-04-15', 18000.00);

-- ─── Support Tickets ─────────────────────────────────────────────────────────

INSERT INTO support_tickets VALUES (1,  6,  3,  'high',   'open',        'Laptop not booting after OS update',         '2024-01-15 09:00', NULL);
INSERT INTO support_tickets VALUES (2,  10, 4,  'medium', 'resolved',    'Phone screen cracked',                       '2024-01-18 11:30', '2024-01-20 14:00');
INSERT INTO support_tickets VALUES (3,  1,  2,  'low',    'open',        'Keyboard key sticking intermittently',       '2024-01-22 10:00', NULL);
INSERT INTO support_tickets VALUES (4,  13, 1,  'high',   'in_progress', 'Server disk usage above 90 percent',         '2024-01-25 08:00', NULL);
INSERT INTO support_tickets VALUES (5,  3,  5,  'medium', 'open',        'Laptop running hot during builds',           '2024-02-01 09:30', NULL);
INSERT INTO support_tickets VALUES (6,  7,  2,  'low',    'resolved',    'Monitor flickering on HDMI input',           '2024-02-03 14:00', '2024-02-05 10:00');
INSERT INTO support_tickets VALUES (7,  14, 1,  'high',   'open',        'Server RAM upgrade required urgently',       '2024-02-10 07:00', NULL);
INSERT INTO support_tickets VALUES (8,  11, 8,  'medium', 'in_progress', 'Phone not syncing with corporate email',     '2024-02-12 15:00', NULL);
INSERT INTO support_tickets VALUES (9,  2,  3,  'high',   'open',        'MacBook display flickering under load',      '2024-02-14 09:00', NULL);
INSERT INTO support_tickets VALUES (10, 5,  10, 'low',    'resolved',    'Trackpad sensitivity too high',              '2024-02-15 11:00', '2024-02-16 09:00');
INSERT INTO support_tickets VALUES (11, 9,  7,  'medium', 'open',        'Monitor not detected on USB-C dock',         '2024-02-18 10:30', NULL);
INSERT INTO support_tickets VALUES (12, 4,  6,  'high',   'open',        'Laptop assigned but not yet configured',     '2024-02-20 09:00', NULL);