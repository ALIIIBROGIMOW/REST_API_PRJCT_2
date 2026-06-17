"""
seed.py — начальные данные для company/
Запускать один раз: python seed.py
"""

import hashlib
import sqlite3
import json
import db 

db.init_db()

conn = sqlite3.connect('company.db')
conn.execute('PRAGMA foreign_keys = ON')


# ── 1. Пользователь (банк авторизуется под этим логином) ──────────────────────

conn.execute('''
    INSERT OR IGNORE INTO users (id, login, password_hash) VALUES (1, ?, ?)
''', (
    'test_bank',
    hashlib.sha256('5959-c2b1-66OfDavmJmM6-62'.encode()).hexdigest()
))


# ── 2. Справочники ─────────────────────────────────────────────────────────────

aid_types = [
    (1, 'Subsidiya', 'Субсидия',         'Subsidy',      'Субсидия'),
    (2, 'Grant',     'Грант',             'Grant',        'Грант'),
    (3, 'Kompensatsiya', 'Компенсация',   'Compensation', 'Компенсация'),
]
conn.executemany('''
    INSERT OR REPLACE INTO aid_types (id, name_uz, name_ru, name_en, name_cyr) VALUES (?,?,?,?,?)
''', aid_types)


privilege_types = [
    (1, 'Nogironlar', 'Инвалиды',              'Disabled persons',  'Инвалидлар'),
    (2, 'Urush veteranlari', 'Ветераны войны', 'War veterans',      'Уруш ветеранлари'),
    (3, 'Koʻp bolali oilalar', 'Многодетные семьи', 'Large families','Кўп болали оилалар'),
]
conn.executemany('''
    INSERT OR REPLACE INTO privilege_types (id, name_uz, name_ru, name_en, name_cyr) VALUES (?,?,?,?,?)
''', privilege_types)


initiative_types = [
    (1, 'INIT-001', 'Tadbirkorlikni qoʻllab-quvvatlash', 'Поддержка предпринимательства', 'Support entrepreneurship', 'Тадбиркорликни қўллаб-қувватлаш'),
    (2, 'INIT-002', 'Qishloq xoʻjaligi', 'Сельское хозяйство', 'Agriculture', 'Қишлоқ хўжалиги'),
    (3, 'INIT-003', 'Eksport dasturi', 'Экспортная программа', 'Export programme', 'Экспорт дастури'),
]
conn.executemany('''
    INSERT OR REPLACE INTO initiatives_types (id, code, name_uz, name_ru, name_en, name_cyr) VALUES (?,?,?,?,?,?)
''', initiative_types)


# ── 3. Скоринги (два завершённых — AGREE и DISAGREE) ──────────────────────────
#    tin подобраны так, чтобы сумма цифр давала нужный результат из run_scoring:
#    чётная сумма → AGREE, нечётная → DISAGREE

conn.execute('''
    INSERT OR IGNORE INTO scorings
        (id, scoring_type, tin, application_number, katm_data,
         status, result, category, report_path, created_at)
    VALUES (1, 'PF-312', '31201995550018', '00000000001',
            '{"active_loans": 2, "overdue_days": 0, "total_debt": 5000000, "monthly_income": 3000000}',
            'DONE', 'AGREE', 2, '/reports/1.pdf', datetime('now'))
''')

conn.execute('''
    INSERT OR IGNORE INTO scorings
        (id, scoring_type, tin, application_number, katm_data,
         status, result, category, report_path, created_at)
    VALUES (2, 'PF-312', '50412984440021', '00000000002',
            '{"active_loans": 4, "overdue_days": 45, "total_debt": 32000000, "monthly_income": 4200000}',
            'DONE', 'DISAGREE', 3, '/reports/2.pdf', datetime('now'))
''')

conn.execute('''
    INSERT OR IGNORE INTO scorings
        (id, scoring_type, tin, application_number, katm_data,
         financial_aid_type, initiative_id, loan_amount, guarantee_amount, guarantee_period,
         status, result, category, report_path, created_at)
    VALUES (3, 'GUARANTEE', '38496685078981', '00000000003',
            '{"active_loans": 0, "overdue_days": 0, "total_debt": 0, "monthly_income": 8500000}',
            1, 1, 20000000, 8000000, 12,
            'DONE', 'AGREE', 2, '/reports/guarantee_3.pdf', datetime('now'))
''')


# ── 4. Привилегии к скорингу №1 ───────────────────────────────────────────────

conn.executemany('''
    INSERT OR IGNORE INTO scoring_privileges
        (scoring_id, full_name, pinfl, position, privilege_type_id)
    VALUES (?,?,?,?,?)
''', [
    (1, 'Иванов Иван Иванович',    '31201995550018', 'Директор',    1),
    (1, 'Петрова Мария Сергеевна', '38496685078981', 'Бухгалтер',   3),
])


# ── 5. Кредит по скорингу №1 (AGREE) ──────────────────────────────────────────

conn.execute('''
    INSERT OR IGNORE INTO loans
        (id, tin, claim_id, application_number, grk_id, created_at)
    VALUES (1, '31201995550018', 1, '00000000001', '123456789012345678', datetime('now'))
''')


# ── 6. Досье по кредиту №1 ────────────────────────────────────────────────────

conn.execute('''
    INSERT OR IGNORE INTO loan_dossiers (
        loan_id, branch_code, head_bank_code, client_name, client_type_code,
        oked, currency_code, loan_type_code, loan_collateral_type,
        purpose_code, purpose_subcode, agreement_date, actual_date,
        repayment_deadline, loan_amount, actually_disbursed_amount, rate,
        source_lending, source_lending_type, credit_status, classification_code,
        principal_debt_past_days, interest_past_days, legal_act_code, loan_grace_period
    ) VALUES (1, '00123', '00100', 'ООО «Тест»', '2',
              '46900', '860', '1', '1',
              '01', '001', '01.01.2025', '05.01.2025',
              '01.01.2027', 20000000, 20000000, 18.5,
              '1', '1', 'active', '1',
              0, 0, '1', 3)
''')


# ── 7. График погашения по кредиту №1 (3 платежа для краткости) ───────────────

conn.executemany('''
    INSERT OR IGNORE INTO loan_schedules
        (loan_id, order_num, return_date, principal_debt, percentage_amount,
         payable_total_amount, principal_balance, days_in_month)
    VALUES (1,?,?,?,?,?,?,?)
''', [
    (1, '01.02.2025',  800000,  307500, 1107500, 19200000, 31),
    (2, '01.03.2025',  814000,  277200, 1091200, 18386000, 28),
    (3, '01.04.2025',  828700,  283000, 1111700, 17557300, 31),
])


# ── 8. Обороты по счетам (кредит №1, несколько операций) ──────────────────────

conn.executemany('''
    INSERT OR IGNORE INTO loan_operations
        (loan_id, account, account_type, debit, credit, operation_date)
    VALUES (1,?,?,?,?,?)
''', [
    ('10100001', 'loan_principal', 20000000,        0, '2025-01-05'),
    ('10100001', 'loan_principal',        0,  800000, '2025-02-01'),
    ('10100001', 'loan_principal',        0,  814000, '2025-03-01'),
    ('10200001', 'loan_interest',         0,  307500, '2025-02-01'),
    ('10200001', 'loan_interest',         0,  277200, '2025-03-01'),
])


conn.commit()
conn.close()

print("✓ Seed завершён.")
