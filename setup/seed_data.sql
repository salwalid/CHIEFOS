-- ============================================================
-- ChiefOS Seed Data
-- Version: 1.0
-- Demo data so dashboards aren't empty after install.
-- All data is generic — replace with your own.
-- ============================================================

-- --------------------------------------------------------
-- Properties (3 demo properties)
-- --------------------------------------------------------
INSERT OR IGNORE INTO properties (id, name, type, status, cleaning_status, critical_notes)
VALUES
    ('PROP_001', '123 Main Street', 'residential', 'occupied', 'clean', 'Long-term tenant. Lease renews annually.'),
    ('PROP_002', '456 Oak Avenue Unit 2', 'residential', 'vacant', 'needs_cleaning', 'Recently vacated. Cleaning scheduled.'),
    ('PROP_003', '789 Commerce Blvd', 'commercial', 'occupied', 'clean', 'Retail tenant. Monthly rent due 1st.');

-- --------------------------------------------------------
-- Contacts (sample contractors)
-- --------------------------------------------------------
INSERT OR IGNORE INTO contacts (name, specialty, contact_info, rating)
VALUES
    ('John Smith Plumbing', 'plumber', '555-0101', 4),
    ('City Electric Co.', 'electrician', '555-0102', 5),
    ('CleanPro Services', 'cleaner', '555-0103', 4),
    ('Green Lawn Care', 'landscaping', '555-0104', 3);

-- --------------------------------------------------------
-- Projects (2 sample active projects)
-- --------------------------------------------------------
INSERT OR IGNORE INTO projects (name, description, status, priority, owner, notes)
VALUES
    ('Property Renovations Q2', 'Kitchen and bathroom updates across portfolio', 'active', 'high', 'Principal', 'Budget approved. Contractor bids being collected.'),
    ('Portfolio Expansion Research', 'Research new acquisition targets in target market', 'active', 'medium', 'Principal', 'Focused on multi-family residential within 50mi radius.');

-- --------------------------------------------------------
-- Todos (sample open items)
-- --------------------------------------------------------
INSERT OR IGNORE INTO todos (title, category, priority, status, due_date, reminder_date, notes)
VALUES
    ('Review insurance renewals', 'finance', 'high', 'open',
     date('now', '+14 days'), date('now', '+7 days'),
     'Check all property insurance policies for renewal dates'),
    ('Schedule Q2 property inspections', 'property', 'medium', 'open',
     date('now', '+30 days'), date('now', '+21 days'),
     'Annual inspection for all properties'),
    ('Follow up with accountant on tax filings', 'finance', 'high', 'open',
     date('now', '+7 days'), date('now', '+3 days'),
     'Q1 filings due soon'),
    ('Research property management software', 'project', 'low', 'open',
     date('now', '+60 days'), date('now', '+45 days'),
     'Compare 3 options and present recommendation');

-- --------------------------------------------------------
-- Subscriptions (sample recurring bills)
-- --------------------------------------------------------
INSERT OR IGNORE INTO subscriptions (name, amount, frequency, category, next_due_date, status, notes)
VALUES
    ('Property Management Software', 49.00, 'monthly', 'software', date('now', '+5 days'), 'active', 'Annual plan billed monthly'),
    ('Cloud Backup Service', 9.99, 'monthly', 'hosting', date('now', '+12 days'), 'active', 'Auto-renews'),
    ('Business Insurance Bundle', 2400.00, 'annual', 'utilities', date('now', '+90 days'), 'active', 'Review coverage before renewal');

-- --------------------------------------------------------
-- Events (upcoming sample events)
-- --------------------------------------------------------
INSERT OR IGNORE INTO events (title, type, start_datetime, location, notes)
VALUES
    ('Lease Review — 123 Main St', 'meeting', date('now', '+10 days'), 'On-site', 'Annual lease renewal discussion with tenant'),
    ('Property Tax Due — Oak Ave', 'deadline', date('now', '+25 days'), 'Online', 'County portal payment'),
    ('Contractor Walkthrough', 'meeting', date('now', '+5 days'), '456 Oak Avenue', 'CleanPro pre-clean assessment for vacant unit');

-- --------------------------------------------------------
-- Financial Transactions (sample entries)
-- --------------------------------------------------------
INSERT OR IGNORE INTO financial_transactions (date, amount, type, category, property_id, description)
VALUES
    (date('now', '-5 days'),  2200.00, 'income',  'rent',     'PROP_001', 'Monthly rent — 123 Main St'),
    (date('now', '-5 days'),  3100.00, 'income',  'rent',     'PROP_003', 'Monthly rent — Commerce Blvd'),
    (date('now', '-10 days'), -320.00, 'expense', 'repair',   'PROP_002', 'Plumbing repair — kitchen sink'),
    (date('now', '-3 days'),  -49.00,  'expense', 'utilities','PROP_001', 'Property management software');

-- --------------------------------------------------------
-- table_principle_week_blueprint (sample weekly rhythm)
-- --------------------------------------------------------
INSERT OR IGNORE INTO table_principle_week_blueprint
    (day_of_week, start_time, end_time, activity_name, focus_type, alpha_protocol)
VALUES
    ('Monday',    '07:00', '09:00', 'Morning Review',      'High Focus', 'Prepare daily brief. Surface urgent todos.'),
    ('Monday',    '09:00', '12:00', 'Deep Work Block',     'High Focus', 'No interruptions. Batch low-priority comms.'),
    ('Monday',    '14:00', '16:00', 'Calls & Meetings',    'Creative',   'Schedule contractor and tenant calls here.'),
    ('Wednesday', '07:00', '09:00', 'Morning Review',      'High Focus', 'Mid-week check. Review project status.'),
    ('Wednesday', '09:00', '12:00', 'Deep Work Block',     'High Focus', 'Complex analysis and decisions.'),
    ('Friday',    '07:00', '09:00', 'Weekly Wrap',         'Creative',   'Review week. Set priorities for next week.'),
    ('Friday',    '09:00', '11:00', 'Finance Review',      'High Focus', 'Review transactions, upcoming bills.'),
    ('Saturday',  '08:00', '10:00', 'Property Operations', 'Creative',   'Handle property tasks and maintenance follow-ups.'),
    ('Sunday',    '09:00', '10:00', 'Week Preview',        'Rest',       'Light review of upcoming week. No deep work.');

-- --------------------------------------------------------
-- context_vault (sample entries)
-- --------------------------------------------------------
INSERT OR IGNORE INTO context_vault (domain, concept, breakthrough, horizon, tags)
VALUES
    ('property', 'Vacancy Lead Time', '30-day notice period means tenant departure gives 30 days to clean, list, and fill. Plan maintenance in week 1, listing in week 2.', 'permanent', 'vacancy,operations'),
    ('finance',  '14-Day Bill Horizon', 'Bank transfers take 3-5 business days. All bills must be queued 14 days before due date, not 5.', 'permanent', 'bills,cashflow');

-- --------------------------------------------------------
-- table_Alpha_Intel (runtime config)
-- --------------------------------------------------------
INSERT OR IGNORE INTO table_Alpha_Intel (key, value)
VALUES
    ('install_date',    date('now')),
    ('chiefos_version', '1.0'),
    ('last_email_id',   '0');
