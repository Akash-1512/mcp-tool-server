-- ============================================================
-- MCP Tool Server — Procurement Domain Seed Data
-- Currency: Mixed (INR for domestic, USD for international)
-- ============================================================

-- ── 1. SPEND CATEGORIES ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS spend_categories (
    id              SERIAL PRIMARY KEY,
    category_code   VARCHAR(20) UNIQUE NOT NULL,
    category_name   VARCHAR(100) NOT NULL,
    parent_category VARCHAR(100),
    spend_type      VARCHAR(20) CHECK (spend_type IN ('direct', 'indirect')),
    commodity_code  VARCHAR(20)
);

INSERT INTO spend_categories (category_code, category_name, parent_category, spend_type, commodity_code) VALUES
('RAW-PKG',   'Raw Material - Packaging',     'Raw Materials',        'direct',   'RM-001'),
('RAW-CHEM',  'Raw Material - Chemicals',     'Raw Materials',        'direct',   'RM-002'),
('RAW-AGRI',  'Raw Material - Agricultural',  'Raw Materials',        'direct',   'RM-003'),
('LOG-TRANS', 'Logistics - Transportation',   'Logistics',            'indirect', 'LG-001'),
('LOG-WARE',  'Logistics - Warehousing',      'Logistics',            'indirect', 'LG-002'),
('IT-SAAS',   'IT - SaaS Subscriptions',      'IT & Technology',      'indirect', 'IT-001'),
('IT-HW',     'IT - Hardware',                'IT & Technology',      'indirect', 'IT-002'),
('MRO-ELEC',  'MRO - Electrical',             'MRO',                  'indirect', 'MR-001'),
('MRO-MECH',  'MRO - Mechanical',             'MRO',                  'indirect', 'MR-002'),
('MKTG-DIG',  'Marketing - Digital',          'Marketing & Services', 'indirect', 'MK-001'),
('MKTG-PRNT', 'Marketing - Print & OOH',      'Marketing & Services', 'indirect', 'MK-002'),
('HR-STAFFG', 'HR - Staffing & Recruitment',  'HR Services',          'indirect', 'HR-001');


-- ── 2. VENDORS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS vendors (
    id              SERIAL PRIMARY KEY,
    vendor_code     VARCHAR(20) UNIQUE NOT NULL,
    vendor_name     VARCHAR(150) NOT NULL,
    category_code   VARCHAR(20) REFERENCES spend_categories(category_code),
    country         VARCHAR(60),
    currency        CHAR(3) CHECK (currency IN ('INR', 'USD', 'EUR', 'AED')),
    tier            VARCHAR(10) CHECK (tier IN ('Tier-1', 'Tier-2', 'Tier-3')),
    status          VARCHAR(20) CHECK (status IN ('active', 'inactive', 'blacklisted', 'under_review')),
    payment_terms   VARCHAR(30),
    contact_email   VARCHAR(150),
    onboarded_date  DATE
);

INSERT INTO vendors (vendor_code, vendor_name, category_code, country, currency, tier, status, payment_terms, contact_email, onboarded_date) VALUES
('VND-001', 'Uflex Limited',               'RAW-PKG',   'India',         'INR', 'Tier-1', 'active',       'Net-30',  'procurement@uflex.in',         '2019-04-01'),
('VND-002', 'Huhtamaki India Pvt Ltd',     'RAW-PKG',   'India',         'INR', 'Tier-1', 'active',       'Net-45',  'supply@huhtamaki.in',          '2018-07-15'),
('VND-003', 'BASF India Limited',          'RAW-CHEM',  'India',         'INR', 'Tier-1', 'active',       'Net-30',  'orders@basf-india.com',        '2017-03-20'),
('VND-004', 'Dow Chemical International', 'RAW-CHEM',  'USA',           'USD', 'Tier-1', 'active',       'Net-60',  'ap@dow.com',                   '2016-11-01'),
('VND-005', 'LANXESS AG',                  'RAW-CHEM',  'Germany',       'USD', 'Tier-2', 'active',       'Net-45',  'procurement@lanxess.com',      '2020-01-10'),
('VND-006', 'Olam Agro India Ltd',         'RAW-AGRI',  'India',         'INR', 'Tier-1', 'active',       'Net-30',  'sourcing@olamagro.in',         '2018-02-28'),
('VND-007', 'Cargill India Pvt Ltd',       'RAW-AGRI',  'India',         'INR', 'Tier-1', 'active',       'Net-30',  'procurement@cargill.com',      '2017-09-05'),
('VND-008', 'DHL Supply Chain India',      'LOG-TRANS', 'India',         'INR', 'Tier-1', 'active',       'Net-45',  'contracts@dhl.in',             '2019-06-01'),
('VND-009', 'Blue Dart Express Ltd',       'LOG-TRANS', 'India',         'INR', 'Tier-2', 'active',       'Net-30',  'enterprise@bluedart.com',      '2020-03-15'),
('VND-010', 'Maersk Line India',           'LOG-TRANS', 'India',         'USD', 'Tier-1', 'active',       'Net-60',  'india.contracts@maersk.com',   '2018-05-20'),
('VND-011', 'Mahindra Logistics Ltd',      'LOG-WARE',  'India',         'INR', 'Tier-2', 'active',       'Net-30',  'warehouse@mahindralogistics.com','2021-01-10'),
('VND-012', 'Salesforce Inc',              'IT-SAAS',   'USA',           'USD', 'Tier-1', 'active',       'Annual',  'enterprise@salesforce.com',    '2020-07-01'),
('VND-013', 'SAP SE',                      'IT-SAAS',   'Germany',       'USD', 'Tier-1', 'active',       'Annual',  'contracts@sap.com',            '2015-01-01'),
('VND-014', 'Zoho Corporation Pvt Ltd',    'IT-SAAS',   'India',         'INR', 'Tier-2', 'active',       'Annual',  'enterprise@zoho.com',          '2021-06-15'),
('VND-015', 'Dell Technologies India',     'IT-HW',     'India',         'INR', 'Tier-1', 'active',       'Net-45',  'largecorp@dell.in',            '2019-08-01'),
('VND-016', 'Havells India Ltd',           'MRO-ELEC',  'India',         'INR', 'Tier-2', 'active',       'Net-30',  'b2b@havells.com',              '2020-11-01'),
('VND-017', 'Siemens India Ltd',           'MRO-ELEC',  'India',         'INR', 'Tier-1', 'active',       'Net-45',  'procurement@siemens.co.in',    '2018-04-10'),
('VND-018', 'SKF India Ltd',               'MRO-MECH',  'India',         'INR', 'Tier-1', 'active',       'Net-30',  'industrial@skf.com',           '2017-12-01'),
('VND-019', 'WPP India Pvt Ltd',           'MKTG-DIG',  'India',         'INR', 'Tier-1', 'active',       'Net-60',  'procurement@wpp.com',          '2020-09-01'),
('VND-020', 'Paragon Print Systems',       'MKTG-PRNT', 'India',         'INR', 'Tier-3', 'under_review', 'Net-30',  'sales@paragonprint.in',        '2022-03-01'),
('VND-021', 'Adecco India Pvt Ltd',        'HR-STAFFG', 'India',         'INR', 'Tier-1', 'active',       'Net-30',  'enterprise@adecco.in',         '2019-01-15'),
('VND-022', 'Brenntag AG',                 'RAW-CHEM',  'Germany',       'USD', 'Tier-2', 'active',       'Net-60',  'asia@brenntag.com',            '2021-08-01'),
('VND-023', 'SCI Logistics',               'LOG-TRANS', 'India',         'INR', 'Tier-3', 'inactive',     'Net-30',  'ops@scilogistics.in',          '2020-05-01'),
('VND-024', 'Reckitt Procurement Svc',     'RAW-PKG',   'UK',            'USD', 'Tier-2', 'blacklisted',  'Net-45',  'n/a',                          '2021-02-01');


-- ── 3. CONTRACTS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contracts (
    id                  SERIAL PRIMARY KEY,
    contract_number     VARCHAR(30) UNIQUE NOT NULL,
    vendor_id           INT REFERENCES vendors(id),
    title               VARCHAR(200),
    contract_value      NUMERIC(15, 2),
    currency            CHAR(3),
    start_date          DATE,
    end_date            DATE,
    auto_renewal        BOOLEAN DEFAULT FALSE,
    status              VARCHAR(20) CHECK (status IN ('active', 'expired', 'terminated', 'draft', 'under_negotiation')),
    owner_department    VARCHAR(60),
    created_at          TIMESTAMP DEFAULT NOW()
);

INSERT INTO contracts (contract_number, vendor_id, title, contract_value, currency, start_date, end_date, auto_renewal, status, owner_department) VALUES
('CTR-2022-001', 1,  'Annual Packaging Supply Agreement — Uflex',          45000000, 'INR', '2022-04-01', '2025-03-31', TRUE,  'active',             'Supply Chain'),
('CTR-2022-002', 3,  'Chemical Raw Materials MSA — BASF India',            62000000, 'INR', '2022-01-01', '2024-12-31', FALSE, 'active',             'R&D Procurement'),
('CTR-2023-001', 4,  'Specialty Chemicals Supply Agreement — Dow',         850000,   'USD', '2023-06-01', '2025-05-31', TRUE,  'active',             'R&D Procurement'),
('CTR-2023-002', 8,  'Logistics Services Agreement — DHL',                 28000000, 'INR', '2023-01-01', '2025-12-31', TRUE,  'active',             'Logistics'),
('CTR-2023-003', 12, 'Salesforce Enterprise License',                      120000,   'USD', '2023-07-01', '2026-06-30', TRUE,  'active',             'IT'),
('CTR-2023-004', 13, 'SAP S/4HANA Cloud Subscription',                    450000,   'USD', '2023-01-01', '2026-12-31', FALSE, 'active',             'IT'),
('CTR-2024-001', 6,  'Agricultural Commodities Framework — Olam',          38000000, 'INR', '2024-01-01', '2024-12-31', FALSE, 'active',             'Supply Chain'),
('CTR-2024-002', 18, 'Bearings & MRO Supply Contract — SKF',               9500000,  'INR', '2024-04-01', '2027-03-31', TRUE,  'active',             'Manufacturing'),
('CTR-2024-003', 21, 'Staffing Services MSA — Adecco',                     15000000, 'INR', '2024-01-01', '2024-12-31', FALSE, 'active',             'HR'),
('CTR-2021-001', 9,  'Express Courier Services — Blue Dart',               7200000,  'INR', '2021-01-01', '2023-12-31', FALSE, 'expired',            'Logistics'),
('CTR-2020-001', 5,  'Specialty Additives Agreement — LANXESS',            290000,   'USD', '2020-06-01', '2023-05-31', FALSE, 'expired',            'R&D Procurement'),
('CTR-2024-004', 10, 'Ocean Freight MSA — Maersk India',                   380000,   'USD', '2024-03-01', '2026-02-28', TRUE,  'active',             'Logistics'),
('CTR-2024-005', 22, 'Chemicals Distribution Agreement — Brenntag',        175000,   'USD', '2024-08-01', '2026-07-31', FALSE, 'under_negotiation',  'R&D Procurement');


-- ── 4. PURCHASE ORDERS ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS purchase_orders (
    id              SERIAL PRIMARY KEY,
    po_number       VARCHAR(30) UNIQUE NOT NULL,
    vendor_id       INT REFERENCES vendors(id),
    contract_id     INT REFERENCES contracts(id),
    category_code   VARCHAR(20) REFERENCES spend_categories(category_code),
    department      VARCHAR(60),
    buyer_name      VARCHAR(100),
    total_amount    NUMERIC(15, 2),
    currency        CHAR(3),
    status          VARCHAR(30) CHECK (status IN ('draft','pending_approval','approved','sent_to_vendor','acknowledged','partially_delivered','delivered','invoiced','paid','cancelled','on_hold')),
    priority        VARCHAR(10) CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    created_at      DATE,
    required_by     DATE,
    notes           TEXT
);

INSERT INTO purchase_orders (po_number, vendor_id, contract_id, category_code, department, buyer_name, total_amount, currency, status, priority, created_at, required_by, notes) VALUES
('PO-2024-0001', 1,  1,    'RAW-PKG',   'Supply Chain',    'Priya Nair',       4200000,  'INR', 'paid',                 'high',     '2024-01-05', '2024-01-25', 'Q1 laminate film replenishment'),
('PO-2024-0002', 3,  2,    'RAW-CHEM',  'R&D Procurement', 'Rahul Deshmukh',   5800000,  'INR', 'paid',                 'high',     '2024-01-10', '2024-02-10', 'Surfactant batch for Q1 production'),
('PO-2024-0003', 4,  3,    'RAW-CHEM',  'R&D Procurement', 'Rahul Deshmukh',   72000,    'USD', 'invoiced',             'high',     '2024-01-15', '2024-02-15', 'Specialty polymer additives'),
('PO-2024-0004', 8,  4,    'LOG-TRANS', 'Logistics',       'Amit Kulkarni',    1850000,  'INR', 'paid',                 'medium',   '2024-01-18', '2024-02-18', 'January distribution run — West India'),
('PO-2024-0005', 6,  7,    'RAW-AGRI',  'Supply Chain',    'Sneha Joshi',      3200000,  'INR', 'delivered',            'high',     '2024-02-01', '2024-02-20', 'Palm oil Q1 tranche'),
('PO-2024-0006', 12, 5,    'IT-SAAS',   'IT',              'Vikram Singh',     28000,    'USD', 'paid',                 'low',      '2024-02-05', '2024-03-01', 'Salesforce additional licences — 20 seats'),
('PO-2024-0007', 2,  NULL, 'RAW-PKG',   'Supply Chain',    'Priya Nair',       2900000,  'INR', 'delivered',            'medium',   '2024-02-10', '2024-03-10', 'Moulded fibre trays for personal care range'),
('PO-2024-0008', 17, NULL, 'MRO-ELEC',  'Manufacturing',   'Deepak Sharma',    680000,   'INR', 'paid',                 'medium',   '2024-02-12', '2024-03-05', 'Switchgear replacements — Pune plant'),
('PO-2024-0009', 10, 12,   'LOG-TRANS', 'Logistics',       'Amit Kulkarni',    95000,    'USD', 'acknowledged',         'high',     '2024-02-20', '2024-04-15', 'Ocean freight — Rotterdam to Nhava Sheva'),
('PO-2024-0010', 7,  NULL, 'RAW-AGRI',  'Supply Chain',    'Sneha Joshi',      4100000,  'INR', 'sent_to_vendor',       'high',     '2024-03-01', '2024-03-20', 'Sunflower oil — Q2 forward purchase'),
('PO-2024-0011', 21, 9,    'HR-STAFFG', 'HR',              'Kavita Menon',     1200000,  'INR', 'approved',             'medium',   '2024-03-05', '2024-04-01', 'Contract workforce — seasonal ramp up'),
('PO-2024-0012', 18, 8,    'MRO-MECH',  'Manufacturing',   'Deepak Sharma',    870000,   'INR', 'partially_delivered',  'medium',   '2024-03-08', '2024-04-08', 'Bearing assemblies — Nasik & Silvassa plants'),
('PO-2024-0013', 22, 13,   'RAW-CHEM',  'R&D Procurement', 'Rahul Deshmukh',   45000,    'USD', 'pending_approval',     'high',     '2024-03-10', '2024-04-10', 'Isopropyl alcohol — bulk order'),
('PO-2024-0014', 5,  NULL, 'RAW-CHEM',  'R&D Procurement', 'Rahul Deshmukh',   38000,    'USD', 'on_hold',              'medium',   '2024-03-12', '2024-05-01', 'HOLD: contract renewal pending — LANXESS'),
('PO-2024-0015', 11, NULL, 'LOG-WARE',  'Logistics',       'Amit Kulkarni',    980000,   'INR', 'approved',             'low',      '2024-03-15', '2024-04-15', 'Warehouse space extension — Bhiwandi'),
('PO-2024-0016', 19, NULL, 'MKTG-DIG',  'Marketing',       'Ananya Rao',       3500000,  'INR', 'invoiced',             'medium',   '2024-03-18', '2024-04-30', 'Digital campaign Q2 — Home Care category'),
('PO-2024-0017', 15, NULL, 'IT-HW',     'IT',              'Vikram Singh',     1450000,  'INR', 'delivered',            'low',      '2024-03-20', '2024-04-20', 'Laptop refresh — 50 units, Finance & HR'),
('PO-2024-0018', 1,  1,    'RAW-PKG',   'Supply Chain',    'Priya Nair',       3800000,  'INR', 'pending_approval',     'high',     '2024-03-22', '2024-04-15', 'Q2 flexible packaging — shampoo SKUs'),
('PO-2024-0019', 8,  4,    'LOG-TRANS', 'Logistics',       'Amit Kulkarni',    2100000,  'INR', 'draft',                'medium',   '2024-03-25', '2024-04-25', 'April distribution run — draft'),
('PO-2024-0020', 13, 6,    'IT-SAAS',   'IT',              'Vikram Singh',     112500,   'USD', 'paid',                 'low',      '2024-01-01', '2024-01-31', 'SAP S/4HANA Q1 subscription payment'),
('PO-2024-0021', 4,  3,    'RAW-CHEM',  'R&D Procurement', 'Rahul Deshmukh',   58000,    'USD', 'cancelled',            'medium',   '2024-02-25', '2024-03-25', 'CANCELLED: superseded by PO-2024-0003 revision'),
('PO-2024-0022', 16, NULL, 'MRO-ELEC',  'Manufacturing',   'Deepak Sharma',    420000,   'INR', 'approved',             'low',      '2024-03-28', '2024-04-28', 'Cable trays and conduits — Haridwar plant');


-- ── 5. PO LINE ITEMS ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS po_line_items (
    id                  SERIAL PRIMARY KEY,
    po_id               INT REFERENCES purchase_orders(id),
    line_number         INT,
    material_code       VARCHAR(30),
    description         VARCHAR(200),
    quantity            NUMERIC(12, 3),
    unit_of_measure     VARCHAR(20),
    unit_price          NUMERIC(12, 4),
    line_total          NUMERIC(15, 2),
    currency            CHAR(3),
    delivery_status     VARCHAR(20) CHECK (delivery_status IN ('pending','in_transit','partially_received','received','rejected')),
    expected_delivery   DATE,
    actual_delivery     DATE
);

INSERT INTO po_line_items (po_id, line_number, material_code, description, quantity, unit_of_measure, unit_price, line_total, currency, delivery_status, expected_delivery, actual_delivery) VALUES
(1,  1, 'PKG-LAM-001', 'BOPP Laminate Film 20 micron',          5000,   'kg',   420,    2100000,  'INR', 'received',           '2024-01-25', '2024-01-24'),
(1,  2, 'PKG-LAM-002', 'Metallised PET Film 12 micron',         5000,   'kg',   420,    2100000,  'INR', 'received',           '2024-01-25', '2024-01-24'),
(2,  1, 'CHEM-SRF-001','Linear Alkylbenzene Sulphonate (LABS)', 20000,  'kg',   185,    3700000,  'INR', 'received',           '2024-02-10', '2024-02-08'),
(2,  2, 'CHEM-SRF-002','Fatty Alcohol Ethoxylate 7EO',          10000,  'kg',   210,    2100000,  'INR', 'received',           '2024-02-10', '2024-02-08'),
(3,  1, 'CHEM-POL-001','Carbopol 940 Polymer',                  2000,   'kg',   18,     36000,    'USD', 'received',           '2024-02-15', '2024-02-14'),
(3,  2, 'CHEM-POL-002','Acrylates Copolymer Emulsion',          2000,   'kg',   18,     36000,    'USD', 'received',           '2024-02-15', '2024-02-20'),
(5,  1, 'AGRI-PLM-001','Refined Bleached Deodorised Palm Oil',  80000,  'kg',   40,     3200000,  'INR', 'received',           '2024-02-20', '2024-02-19'),
(7,  1, 'PKG-TRY-001', 'Moulded Fibre Tray 200mm x 150mm',     500000, 'units', 3.80,  1900000,  'INR', 'received',           '2024-03-10', '2024-03-09'),
(7,  2, 'PKG-TRY-002', 'Moulded Fibre Lid 200mm x 150mm',      300000, 'units', 3.33,  1000000,  'INR', 'received',           '2024-03-10', '2024-03-09'),
(9,  1, 'LOG-FCL-001', 'FCL 40HQ Rotterdam → Nhava Sheva',      2,      'container', 42500, 85000, 'USD', 'in_transit',       '2024-04-15', NULL),
(9,  2, 'LOG-FCL-002', 'Customs Clearance & Port Handling',     1,      'lumpsum',10000, 10000,   'USD', 'pending',            '2024-04-15', NULL),
(12, 1, 'MRO-BRG-001', 'Deep Groove Ball Bearing 6205-2RS',    500,    'units', 520,    260000,   'INR', 'received',           '2024-04-08', '2024-04-06'),
(12, 2, 'MRO-BRG-002', 'Spherical Roller Bearing 22210E',      200,    'units', 1550,   310000,   'INR', 'partially_received',  '2024-04-08', NULL),
(12, 3, 'MRO-BRG-003', 'Taper Roller Bearing 32210',           300,    'units', 1000,   300000,   'INR', 'pending',            '2024-04-08', NULL),
(13, 1, 'CHEM-IPA-001','Isopropyl Alcohol 99.9% Pure',         10000,  'kg',    4.50,   45000,    'USD', 'pending',            '2024-04-10', NULL),
(16, 1, 'MKTG-DIG-001','Digital Media Buying — Meta/Google',   1,      'campaign', 2500000, 2500000,'INR','pending',           '2024-04-30', NULL),
(16, 2, 'MKTG-DIG-002','Creative Production — Video 30s',      4,      'units', 250000, 1000000,  'INR', 'pending',            '2024-04-30', NULL),
(17, 1, 'IT-LAP-001',  'Dell Latitude 5540 i5 16GB 512GB SSD', 50,     'units', 29000,  1450000,  'INR', 'received',           '2024-04-20', '2024-04-18'),
(20, 1, 'IT-SAP-Q1',   'SAP S/4HANA Cloud Q1 2024 Invoice',   1,      'invoice',112500,112500,   'USD', 'received',           '2024-01-31', '2024-01-30');


-- ── 6. APPROVAL WORKFLOW ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS approval_workflow (
    id              SERIAL PRIMARY KEY,
    po_id           INT REFERENCES purchase_orders(id),
    level           INT,
    approver_name   VARCHAR(100),
    approver_role   VARCHAR(100),
    decision        VARCHAR(20) CHECK (decision IN ('pending', 'approved', 'rejected', 'escalated')),
    decided_at      TIMESTAMP,
    comments        TEXT
);

INSERT INTO approval_workflow (po_id, level, approver_name, approver_role, decision, decided_at, comments) VALUES
-- PO-2024-0011 (approved, 2-level)
(11, 1, 'Kavita Menon',   'Category Manager — HR',         'approved',  '2024-03-06 10:15:00', 'Seasonal demand confirmed'),
(11, 2, 'Rajesh Iyer',    'Head of Procurement',           'approved',  '2024-03-07 09:30:00', 'Within budget. Proceed.'),
-- PO-2024-0013 (pending approval)
(13, 1, 'Rahul Deshmukh', 'Category Manager — Chemicals',  'approved',  '2024-03-11 14:00:00', 'Validated against MRP'),
(13, 2, 'Rajesh Iyer',    'Head of Procurement',           'pending',   NULL,                  NULL),
-- PO-2024-0018 (pending approval)
(18, 1, 'Priya Nair',     'Category Manager — Packaging',  'approved',  '2024-03-23 11:30:00', 'Q2 plan aligned'),
(18, 2, 'Rajesh Iyer',    'Head of Procurement',           'pending',   NULL,                  NULL),
-- PO-2024-0015 (approved, 1-level)
(15, 1, 'Amit Kulkarni',  'Logistics Manager',             'approved',  '2024-03-16 16:00:00', 'Capacity crunch confirmed'),
-- PO-2024-0022 (approved, 1-level)
(22, 1, 'Deepak Sharma',  'Plant Maintenance Manager',     'approved',  '2024-03-29 10:00:00', 'Planned maintenance cycle'),
-- PO-2024-0021 (cancelled — rejection trail)
(21, 1, 'Rahul Deshmukh', 'Category Manager — Chemicals',  'approved',  '2024-02-26 09:00:00', NULL),
(21, 2, 'Rajesh Iyer',    'Head of Procurement',           'rejected',  '2024-02-27 11:00:00', 'Duplicate of PO-2024-0003. Cancel and reissue.');


-- ── INDEXES ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_po_status        ON purchase_orders(status);
CREATE INDEX IF NOT EXISTS idx_po_vendor        ON purchase_orders(vendor_id);
CREATE INDEX IF NOT EXISTS idx_po_currency      ON purchase_orders(currency);
CREATE INDEX IF NOT EXISTS idx_po_created       ON purchase_orders(created_at);
CREATE INDEX IF NOT EXISTS idx_vendor_status    ON vendors(status);
CREATE INDEX IF NOT EXISTS idx_vendor_tier      ON vendors(tier);
CREATE INDEX IF NOT EXISTS idx_contract_status  ON contracts(status);
CREATE INDEX IF NOT EXISTS idx_lineitems_po     ON po_line_items(po_id);
CREATE INDEX IF NOT EXISTS idx_approval_po      ON approval_workflow(po_id);