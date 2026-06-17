import sqlite3 


conn = sqlite3.connect('company.db', check_same_thread=False) 

conn.row_factory = sqlite3.Row
conn.execute('PRAGMA foreign_keys = ON')


#запускается из app.py
def init_db():
    with conn: 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id                      INTEGER PRIMARY KEY AUTOINCREMENT, 
                        login                   TEXT NOT NULL,  
                        password_hash           TEXT NOT NULL
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS tokens (
                        id                      INTEGER PRIMARY KEY AUTOINCREMENT, 
                        access_token            TEXT NOT NULL,  
                        expire_date             TEXT NOT NULL,
                        user_id                 INTEGER UNIQUE NOT NULL,
                        
                        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS aid_types (
                        id                      INTEGER PRIMARY KEY,  
                        name_uz                    TEXT NOT NULL,
                        name_ru                    TEXT NOT NULL,
                        name_en                    TEXT NOT NULL,
                        name_cyr                   TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS privilege_types (
                        id                      INTEGER PRIMARY KEY,  
                        name_uz                    TEXT NOT NULL,
                        name_ru                    TEXT NOT NULL,
                        name_en                    TEXT NOT NULL,
                        name_cyr                   TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS initiatives_types (
                        id                      INTEGER PRIMARY KEY,  
                        code                    TEXT UNIQUE NOT NULL, 
                        name_uz                    TEXT NOT NULL,
                        name_ru                    TEXT NOT NULL,
                        name_en                    TEXT NOT NULL,
                        name_cyr                   TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS scorings (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        scoring_type        TEXT NOT NULL,
                        tin                 TEXT NOT NULL,
                        application_number  TEXT NOT NULL,
                        description         TEXT,
                        katm_data           TEXT,
                        financial_aid_type  INTEGER,
                        initiative_id       INTEGER,
                        loan_amount         INTEGER,
                        guarantee_amount    INTEGER,
                        guarantee_period    INTEGER,
                        status              TEXT NOT NULL,
                        result              TEXT,
                        category            INTEGER,
                        report_path         TEXT,
                        created_at          TEXT NOT NULL,
                        updated_at          TEXT
                    );
                ''')
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS scoring_privileges (
                        id                INTEGER PRIMARY KEY AUTOINCREMENT,
                        scoring_id        INTEGER NOT NULL,
                        full_name         TEXT,
                        pinfl             TEXT,
                        position          TEXT,
                        privilege_type_id INTEGER,
                        FOREIGN KEY(scoring_id) REFERENCES scorings(id) ON DELETE CASCADE
                    );
                ''')
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS loans (
                        id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                        tin                TEXT NOT NULL,
                        claim_id           INTEGER NOT NULL UNIQUE,
                        application_number TEXT NOT NULL,
                        grk_id             TEXT NOT NULL UNIQUE,
                        created_at         TEXT NOT NULL,
                        FOREIGN KEY(claim_id) REFERENCES scorings(id)
                    );
                ''')
         

        conn.execute('''
            CREATE TABLE IF NOT EXISTS loan_schedules (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id              INTEGER NOT NULL,
                order_num            INTEGER,
                return_date          TEXT,
                principal_debt       INTEGER,
                percentage_amount    INTEGER,
                payable_total_amount INTEGER,
                principal_balance    INTEGER,
                days_in_month        INTEGER,
                FOREIGN KEY(loan_id) REFERENCES loans(id)
            );
        ''')

        conn.execute('''
            CREATE TABLE IF NOT EXISTS loan_accounts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id       INTEGER NOT NULL,
                period_start  TEXT NOT NULL,
                period_end    TEXT NOT NULL,
                account       TEXT,
                account_type  TEXT,
                balance_start INTEGER,
                balance_end   INTEGER,
                operations    TEXT,
                FOREIGN KEY(loan_id) REFERENCES loans(id)
            );
        ''')        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS loan_dossiers (
                id                        INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id                   INTEGER NOT NULL UNIQUE,
                branch_code               TEXT,
                head_bank_code            TEXT,
                client_name               TEXT,
                client_type_code          TEXT,
                oked                      TEXT,
                currency_code             TEXT,
                loan_type_code            TEXT,
                loan_collateral_type      TEXT,
                purpose_code              TEXT,
                purpose_subcode           TEXT,
                agreement_date            TEXT,
                actual_date               TEXT,
                repayment_deadline        TEXT,
                loan_amount               INTEGER,
                actually_disbursed_amount INTEGER,
                rate                      REAL,
                source_lending            TEXT,
                source_lending_type       TEXT,
                credit_status             TEXT,
                classification_code       TEXT,
                principal_debt_past_days  INTEGER,
                interest_past_days        INTEGER,
                legal_act_code            TEXT,
                loan_grace_period         INTEGER,
                FOREIGN KEY(loan_id) REFERENCES loans(id)
            );
        ''')
         
        
        conn.execute('''
            CREATE TABLE IF NOT EXISTS loan_operations (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id        INTEGER NOT NULL,
                account        TEXT NOT NULL,
                account_type   TEXT,
                debit          INTEGER,
                credit         INTEGER,
                operation_date TEXT,
                FOREIGN KEY(loan_id) REFERENCES loans(id)
            );
        ''') 

#################
def get_alldossiers() -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_dossiers').fetchall()
    return [dict(r) for r in rows]

#################
def get_all_operations() -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_operations').fetchall()
    return [dict(r) for r in rows]

#################
def get_all_scorings() -> list[dict]:
    rows = conn.execute('SELECT * FROM scorings').fetchall()
    return [dict(r) for r in rows]
#################
def get_all_schedules() -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_schedules').fetchall()
    return [dict(r) for r in rows]

#############

def get_users_with_tokens() -> list[dict]:
    rows = conn.execute('''
        SELECT users.login, tokens.access_token, tokens.expire_date
        FROM users
        LEFT JOIN tokens ON tokens.user_id = users.id
    ''').fetchall()
    return [dict(r) for r in rows] 





def _date_to_iso(date_str: str) -> str:
    day, month, year = date_str.split('.')
    return f'{year}-{month}-{day}'


def get_loan_operations( loan_id: int, period_start: str, period_end: str) -> list[dict]:
    
 
    start = _date_to_iso(period_start)
    end = _date_to_iso(period_end)
    
    rows = conn.execute(
        '''
        SELECT *
        FROM loan_operations
        WHERE loan_id = ?
          AND operation_date >= ?
          AND operation_date <= ?
        ORDER BY operation_date
        ''',
        (loan_id, start, end)
    ).fetchall()

    return [dict(r) for r in rows]


def save_loan_operations(loan_id: int, operations: list[dict]):
    with conn:
        conn.execute(
            'DELETE FROM loan_operations WHERE loan_id = ?',
            (loan_id,)
        )

        for op in operations:
            date = _date_to_iso(op['operation_date'])
            
            conn.execute(
                '''
                INSERT INTO loan_operations(
                    loan_id,
                    account,
                    account_type,
                    debit,
                    credit,
                    operation_date
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    loan_id,
                    op.get('account'),
                    op.get('account_type'),
                    op.get('debit'),
                    op.get('credit'),
                    date,
                )
            )




#################




def save_loan_dossier(loan_id: int, data: dict):
    with conn:
        conn.execute('''
            INSERT OR REPLACE INTO loan_dossiers(
                loan_id, branch_code, head_bank_code, client_name,
                client_type_code, oked, currency_code, loan_type_code,
                loan_collateral_type, purpose_code, purpose_subcode,
                agreement_date, actual_date, repayment_deadline,
                loan_amount, actually_disbursed_amount, rate,
                source_lending, source_lending_type, credit_status,
                classification_code, principal_debt_past_days,
                interest_past_days, legal_act_code, loan_grace_period
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            loan_id,
            data.get('branch_code'),
            data.get('head_bank_code'),
            data.get('client_name'),
            data.get('client_type_code'),
            data.get('oked'),
            data.get('currency_code'),
            data.get('loan_type_code'),
            data.get('loan_collateral_type'),
            data.get('purpose_code'),
            data.get('purpose_subcode'),
            data.get('agreement_date'),
            data.get('actual_date'),
            data.get('repayment_deadline'),
            data.get('loan_amount'),
            data.get('actually_disbursed_amount'),
            data.get('rate'),
            data.get('source_lending'),
            data.get('source_lending_type'),
            data.get('credit_status'),
            data.get('classification_code'),
            data.get('principal_debt_past_days'),
            data.get('interest_past_days'),
            data.get('legal_act_code'),
            data.get('loan_grace_period'),
        ))

def get_loan_dossier(loan_id: int) -> dict | None:
    row = conn.execute(
        'SELECT * FROM loan_dossiers WHERE loan_id = ?', (loan_id,)
    ).fetchone()
    return dict(row) if row else None



def save_loan_schedule(loan_id: int, payments: list[dict]):
    with conn:
        conn.execute('DELETE FROM loan_schedules WHERE loan_id = ?', (loan_id,))
        for p in payments:
            conn.execute('''
                INSERT INTO loan_schedules(
                    loan_id, order_num, return_date, principal_debt,
                    percentage_amount, payable_total_amount,
                    principal_balance, days_in_month
                ) VALUES (?,?,?,?,?,?,?,?)
            ''', (
                loan_id,
                p.get('order_num'),
                p.get('return_date'),
                p.get('principal_debt'),
                p.get('percentage_amount'),
                p.get('payable_total_amount'),
                p.get('principal_balance'),
                p.get('days_in_month'),
            ))

def get_loan_schedule(loan_id: int) -> list[dict]:
    rows = conn.execute(
        'SELECT * FROM loan_schedules WHERE loan_id = ? ORDER BY order_num',
        (loan_id,)
    ).fetchall()
    return [dict(r) for r in rows]





def get_all_loans() -> list[dict]:
    rows = conn.execute('SELECT * FROM loans').fetchall()
    return [dict(r) for r in rows]



###############









        

def create_loan(
    tin: int | str,
    claim_id: int,
    application_number: int | str,
    grk_id: str,
) -> int:
    with conn:
        cursor = conn.execute("""
            INSERT INTO loans(
                tin, 
                claim_id, 
                application_number, 
                grk_id, 
                created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (            
            str(tin),
            claim_id, 
            str(application_number), 
            grk_id))
        assert cursor.lastrowid is not None #чтобы отладчики не ругались на невозможный случай...
        return cursor.lastrowid


def get_loan_by_claim_id(claim_id: int) -> dict | None:
    row = conn.execute(
        'SELECT * FROM loans WHERE claim_id = ?', (claim_id,)
    ).fetchone()
    return dict(row) if row else None
        
        
        
################################
def create_scoring(
    scoring_type: str,
    tin: str|int,
    application_number: str|int,
    katm_data: str,
    description: str | None = None,
    financial_aid_type: int | None = None,
    initiative_id: int | None = None,
    loan_amount: int | None = None,
    guarantee_amount: int | None = None,
    guarantee_period: int | None = None,
) -> int:
    with conn:
        cursor = conn.execute("""
            INSERT INTO scorings(
                scoring_type,
                tin,
                application_number,
                katm_data,
                description,
                financial_aid_type,
                initiative_id,
                loan_amount,
                guarantee_amount,
                guarantee_period,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', datetime('now'))
        """, (
            scoring_type,
            str(tin),
            str(application_number),
            katm_data,
            description,
            financial_aid_type,
            initiative_id,
            loan_amount,
            guarantee_amount,
            guarantee_period,
        ))
        assert cursor.lastrowid is not None #чтобы отладчики не ругались на невозможный случай...
        return cursor.lastrowid


def get_scoring(scoring_id: int) -> dict | None:
    row = conn.execute(
        'SELECT * FROM scorings WHERE id = ?', (scoring_id,)
    ).fetchone()
    return dict(row) if row else None


def save_scoring_result(
    scoring_id: int,
    result: str,
    category: int,
    report_path: str,
):
    with conn:
        conn.execute("""
            UPDATE scorings SET
                result     = ?,
                category   = ?,
                report_path = ?,
                status     = 'DONE',
                updated_at = datetime('now')
            WHERE id = ?
        """, (result, category, report_path, scoring_id))


def save_scoring_privileges(scoring_id: int, privileges: list[dict]):
    with conn:
        conn.execute(
            'DELETE FROM scoring_privileges WHERE scoring_id = ?', (scoring_id,)
        )
        for p in privileges:
            conn.execute("""
                INSERT INTO scoring_privileges(
                    scoring_id, full_name, pinfl, position, privilege_type_id
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                scoring_id,
                p['full_name'],
                str(p['pinfl']),
                p['position'],
                p['privilege_type_id'],
            ))


def get_scoring_privileges(scoring_id: int) -> list[dict]:
    rows = conn.execute(
        'SELECT * FROM scoring_privileges WHERE scoring_id = ?', (scoring_id,)
    ).fetchall()
    return [dict(r) for r in rows]
############################################
 

#######################
def get_all_scoring_privileges() -> list[dict]:
    rows = conn.execute('SELECT * FROM scoring_privileges').fetchall()
    return [dict(r) for r in rows]
###########################
LANG_COL = {
    'UZ': 'name_uz',
    'RU': 'name_ru', 
    'EN': 'name_en',
    'UZ-CYRL': 'name_cyr'
}

def _lang_col(lang: str) -> str:
    return LANG_COL.get(lang.upper(), 'name_ru')

# --- aid_types ---

def save_aid_type(code: int, name_uz: str, name_ru: str, name_en: str, name_cyr: str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO aid_types (id, name_uz, name_ru, name_en, name_cyr, last_update_date) VALUES (?, ?, ?, ?, ?, datetime("now"))',
            (code, name_uz, name_ru, name_en, name_cyr)
        )

def get_aid_types(lang: str) -> list[dict | None]:
    col = _lang_col(lang)
    rows = conn.execute(f'SELECT id, {col} as name FROM aid_types').fetchall()
    return [dict(r) for r in rows]

def get_aid_type(code: int, lang: str) -> dict | None:
    col = _lang_col(lang)
    row = conn.execute(f'SELECT id, {col} as name FROM aid_types WHERE id = ?', (code,)).fetchone()
    return dict(row) if row else None


# --- privilege_types ---

def save_privilege_type(code: int, name_uz: str, name_ru: str, name_en: str, name_cyr: str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO privilege_types (id, name_uz, name_ru, name_en, name_cyr, last_update_date) VALUES (?, ?, ?, ?, ?, datetime("now"))',
            (code, name_uz, name_ru, name_en, name_cyr)
        )

def get_privilege_types(lang: str) -> list[dict | None]:
    col = _lang_col(lang)
    rows = conn.execute(f'SELECT id, {col} as name FROM privilege_types').fetchall()
    return [dict(r) for r in rows]

def get_privilege_type(code: int, lang: str) -> dict | None:
    col = _lang_col(lang)
    row = conn.execute(f'SELECT id, {col} as name FROM privilege_types WHERE id = ?', (code,)).fetchone()
    return dict(row) if row else None


# --- initiatives_types ---

def save_initiative_type(id: int, code: str, name_uz: str, name_ru: str, name_en: str, name_cyr: str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO initiatives_types (id, code, name_uz, name_ru, name_en, name_cyr, last_update_date) VALUES (?, ?, ?, ?, ?, ?, datetime("now"))',
            (id, code, name_uz, name_ru, name_en, name_cyr)
        )

def get_initiative_types(lang: str) -> list[dict | None]:
    col = _lang_col(lang)
    rows = conn.execute(f'SELECT id, code, {col} as name FROM initiatives_types').fetchall()
    return [dict(r) for r in rows]

def get_initiative_type_by_id(id: int, lang: str) -> dict | None:
    col = _lang_col(lang)
    row = conn.execute(f'SELECT id, code, {col} as name FROM initiatives_types WHERE id = ?', (id,)).fetchone()
    return dict(row) if row else None

def get_initiative_type_by_code(code: str, lang: str) -> dict | None:
    col = _lang_col(lang)
    row = conn.execute(f'SELECT id, code, {col} as name FROM initiatives_types WHERE code = ?', (code,)).fetchone()
    return dict(row) if row else None


        
        
        

def get_user_by_username(user_name: str) -> dict | None:
    with conn:
        user = conn.execute(
            'SELECT id, login, password_hash from users where login = ?', 
            (user_name,)
        ).fetchone()
        return dict(user) if user is not None else None
     
     
def add_token(access_token : str, expire_date : str, user_id : int):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO tokens (access_token, expire_date, user_id) VALUES (?, ?, ?)', 
            (access_token, expire_date, user_id)
        )
 
               
def get_token(access_token : str) -> dict | None:
    with conn:
        token = conn.execute('SELECT access_token, expire_date FROM tokens WHERE access_token = ?', 
                            (access_token,)).fetchone()
        return dict(token) if token is not None else None
 
 
