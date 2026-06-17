"""
seed.py — начальные данные для bank/
Запускать один раз: python seed.py
"""

import hashlib
import sqlite3
import json
import db 

db.init_db()

conn = sqlite3.connect('bank.db')
conn.execute('PRAGMA foreign_keys = ON')


conn.execute('''
    INSERT OR IGNORE INTO scorings
        (company_scoring_id, scoring_type, tin, application_number,
         status, result, category, response_link, created_at)
    VALUES (1, 'PF-312', '31201995550018', '00000000001',
            'DONE', 'AGREE', 2, '/reports/1.pdf', datetime('now'))
''')

 

conn.executemany('''
    INSERT OR IGNORE INTO scoring_privileges
        (company_scoring_id, full_name, pinfl, position, privilege_type_id)
    VALUES (?,?,?,?,?)
''', [
    (1, 'Иванов Иван Иванович',    '31201995550018', 'Директор',    1),
    (1, 'Петрова Мария Сергеевна', '38496685078981', 'Бухгалтер',   3),
])

 
conn.execute('''
    INSERT OR IGNORE INTO loans
        (company_loan_id, tin, company_scoring_id, application_number, grk_id, created_at)
    VALUES (1, '31201995550018', 1, '00000000001', '123456789012345678', datetime('now'))
''')



conn.commit()
conn.close()

print("✓ Seed завершён.")