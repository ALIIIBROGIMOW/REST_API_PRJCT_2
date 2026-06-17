import sqlite3 

conn = sqlite3.connect('bank.db', check_same_thread=False)

conn.row_factory = sqlite3.Row
conn.execute('PRAGMA foreign_keys = ON')


#запускается из app.py
def init_db():
    with conn: 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS token (
                        id                      INTEGER PRIMARY KEY, 
                        access_token            TEXT NOT NULL,  
                        expire_date             TEXT NOT NULL
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS aid_types (
                        id                      INTEGER PRIMARY KEY,  
                        name                    TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS privilege_types (
                        id                      INTEGER PRIMARY KEY,  
                        name                    TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS initiatives_types (
                        id                      INTEGER PRIMARY KEY,  
                        code                    TEXT UNIQUE NOT NULL,
                        name                    TEXT NOT NULL,
                        last_update_date        TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS scorings  (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_scoring_id  INTEGER UNIQUE NOT NULL, 
                        
                        scoring_type TEXT NOT NULL,
                        
                        application_number  TEXT NOT NULL,
                        tin                 TEXT NOT NULL,
                        
                        status              TEXT NOT NULL,
                        
                        category            INTEGER,
                        result              TEXT,
                        response_link       TEXT,
                        
                        created_at          TEXT NOT NULL,
                        updated_at          TEXT
                    );
                    '''
                    ) 
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS scoring_privileges (
                        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_scoring_id          INTEGER NOT NULL,

                        full_name           TEXT,
                        pinfl               TEXT,
                        position            TEXT,
                        privilege_type_id   INTEGER,

                        FOREIGN KEY(company_scoring_id) REFERENCES scorings(company_scoring_id) ON DELETE CASCADE
                    );
                    '''
                    ) 
        
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS loans (
                        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                        company_loan_id       INTEGER NOT NULL UNIQUE,  -- ID кредита от Компании
                        
                        
                        company_scoring_id    INTEGER NOT NULL,
                        tin                   TEXT NOT NULL,
                        application_number    TEXT NOT NULL,
                        grk_id                TEXT NOT NULL,     -- 18-значный номер от ЦБ
                        created_at            TEXT NOT NULL,
                        
 
                        branch_code              TEXT,
                        head_bank_code           TEXT,
                        client_name              TEXT,
                        client_type_code         TEXT,
                        oked                     TEXT,
                        currency_code            TEXT,
                        loan_type_code           TEXT,
                        loan_collateral_type     TEXT,
                        purpose_code             TEXT,
                        purpose_subcode          TEXT,
                        agreement_date           TEXT,
                        actual_date              TEXT,
                        repayment_deadline       TEXT,
                        loan_amount              INTEGER,
                        actually_disbursed_amount INTEGER,
                        rate                     REAL,
                        source_lending           TEXT,
                        source_lending_type      TEXT,
                        credit_status            TEXT,
                        classification_code      TEXT,
                        principal_debt_past_days INTEGER,
                        interest_past_days       INTEGER,
                        legal_act_code           TEXT,
                        loan_grace_period        INTEGER,
                        
                        
                        FOREIGN KEY(company_scoring_id) REFERENCES scorings(company_scoring_id)
                    );
                    '''
                    ) 


        conn.execute('''
                    CREATE TABLE IF NOT EXISTS loan_schedule (
                        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                        loan_id               INTEGER NOT NULL,
                        order_num             INTEGER,
                        return_date           TEXT,
                        principal_debt        INTEGER,
                        percentage_amount     INTEGER,
                        payable_total_amount  INTEGER,
                        principal_balance     INTEGER,
                        days_in_month         INTEGER,
                        FOREIGN KEY(loan_id) REFERENCES loans(company_loan_id)
                    );
                    '''
                    ) 
        
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS loan_accounts (
                        id                INTEGER PRIMARY KEY AUTOINCREMENT,
                        loan_id           INTEGER NOT NULL,
                        period_start      TEXT,
                        period_end        TEXT,
                        account           TEXT,
                        account_type      TEXT,
                        balance_start     INTEGER,
                        balance_end       INTEGER,
                        operations        TEXT,  
                        FOREIGN KEY(loan_id) REFERENCES loans(company_loan_id) 
                    );
                    '''
                    ) 
        
def get_all_aid_types() -> list[dict]:
    rows = conn.execute('SELECT * FROM aid_types').fetchall()
    return [dict(r) for r in rows]
        
def get_all_privilege_types() -> list[dict]:
    rows = conn.execute('SELECT * FROM privilege_types').fetchall()
    return [dict(r) for r in rows]

def get_all_initiative_types() -> list[dict]:
    rows = conn.execute('SELECT * FROM initiatives_types').fetchall()
    return [dict(r) for r in rows]
        
        
        
        
        
        
        
        
        
        
        
def create_loan_account(
    loan_id: int,
    period_start : str,
    period_end: str,
    account: str,
    account_type: str,
    balance_start: int,
    balance_end: int,
    operations: str,  
):
    with conn:
        conn.execute("""
            INSERT INTO loan_accounts(
                loan_id,
                period_start,
                period_end,
                account,
                account_type,
                balance_start,
                balance_end,
                operations
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loan_id,
            period_start,
            period_end,
            account,
            account_type,
            balance_start,
            balance_end,
            operations,  
        ))


def create_loan_schedule(
    loan_id: int,
    order_num: int,
    return_date: str,
    principal_debt: int,
    percentage_amount: int,
    payable_total_amount: int,
    principal_balance: int,
    days_in_month: int
):
    with conn:
        conn.execute("""
            INSERT INTO loan_schedule(
                loan_id,
                order_num,
                return_date,
                principal_debt,
                percentage_amount,
                payable_total_amount,
                principal_balance,
                days_in_month
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            loan_id,
            order_num,
            return_date,
            principal_debt,
            percentage_amount,
            payable_total_amount,
            principal_balance,
            days_in_month
        ))



def add_loan_dossier(
    company_loan_id: int,
    branch_code: str,
    head_bank_code: str,
    client_name: str,
    client_type_code: str,
    oked: str,
    currency_code: str,
    loan_type_code: str,
    loan_collateral_type: str,
    purpose_code: str,
    purpose_subcode: str,
    agreement_date: str,
    actual_date: str,
    repayment_deadline: str,
    loan_amount: int,
    actually_disbursed_amount: int,
    rate: float,
    source_lending: str,
    source_lending_type: str,
    credit_status: str,
    classification_code: str,
    principal_debt_past_days: int,
    interest_past_days: int,
    legal_act_code: str,
    loan_grace_period: int
):
    with conn:
        conn.execute("""
            UPDATE loans SET
                branch_code               = ?,
                head_bank_code            = ?,
                client_name               = ?,
                client_type_code          = ?,
                oked                      = ?,
                currency_code             = ?,
                loan_type_code            = ?,
                loan_collateral_type      = ?,
                purpose_code              = ?,
                purpose_subcode           = ?,
                agreement_date            = ?,
                actual_date               = ?,
                repayment_deadline        = ?,
                loan_amount               = ?,
                actually_disbursed_amount = ?,
                rate                      = ?,
                source_lending            = ?,
                source_lending_type       = ?,
                credit_status             = ?,
                classification_code       = ?,
                principal_debt_past_days  = ?,
                interest_past_days        = ?,
                legal_act_code            = ?,
                loan_grace_period         = ?
            WHERE company_loan_id = ?
        """, (
            branch_code,
            head_bank_code,
            client_name,
            client_type_code,
            oked,
            currency_code,
            loan_type_code,
            loan_collateral_type,
            purpose_code,
            purpose_subcode,
            agreement_date,
            actual_date,
            repayment_deadline,
            loan_amount,
            actually_disbursed_amount,
            rate,
            source_lending,
            source_lending_type,
            credit_status,
            classification_code,
            principal_debt_past_days,
            interest_past_days,
            legal_act_code,
            loan_grace_period,
            company_loan_id
        ))


def create_loan(
                company_scoring_id: int,
                tin : str|int,
                application_number : str,    
                company_loan_id : int,
                grk_id: str|int 
            ):
    grk_id = str(grk_id)
    tin = str(tin)
    
    with conn:
        conn.execute("""
            INSERT INTO loans( 
                company_scoring_id,
                tin,
                application_number,
                company_loan_id,
                grk_id,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            company_scoring_id,
            tin,
            application_number, 
            company_loan_id,
            grk_id
        ))
    

def create_scoring(company_scoring_id : int, 
                   application_number : str, 
                   scoring_type : str , 
                   tin : str):
    with conn:
        conn.execute("""
            INSERT INTO scorings(
                scoring_type,
                company_scoring_id,
                application_number,
                tin,
                created_at,
                status
            )
            VALUES (?, ?, ?, ?, datetime('now'), ?)
        """, (
            scoring_type,
            company_scoring_id,
            application_number,
            tin,
            "CREATED"
        ))

def save_scoring_result(
    company_scoring_id : int,
    category : int,
    result : str,
    response_link : str    
):
    with conn:
        conn.execute("""
            UPDATE scorings
            SET
                category=?,
                result=?,
                response_link=?,
                status=?,
                updated_at=datetime('now')
            WHERE company_scoring_id=?
        """, (
            category,
            result,
            response_link,
            result,
            company_scoring_id
        ))


def get_scoring_by_company_id(company_scoring_id : int):
    with conn:
        data = conn.execute('''SELECT 
                            id, 
                            company_scoring_id,
                            scoring_type,
                            application_number,
                            tin,
                            status,
                            category,
                            result,
                            response_link,
                            created_at,        
                            updated_at 
                            FROM scorings WHERE company_scoring_id = ?''', 
                            (company_scoring_id,)).fetchone()
        return dict(data)
 
  



def add_privilege(company_scoring_id: int, full_name: str, pinfl: str | int, position: str, privilege_type_id: int):
    with conn:
        conn.execute("""
            INSERT INTO scoring_privileges(
                company_scoring_id,
                full_name,
                pinfl,
                position,
                privilege_type_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (company_scoring_id, full_name, str(pinfl), position, privilege_type_id))
    

def save_privileges(company_scoring_id : int, privileges : list ):

    with conn:
        conn.execute(
            "DELETE FROM scoring_privileges WHERE company_scoring_id=?",
            (company_scoring_id,)
        )

        for p in privileges:
            conn.execute("""
                INSERT INTO scoring_privileges(
                    company_scoring_id,
                    full_name,
                    pinfl,
                    position,
                    privilege_type_id
                )
                VALUES (?, ?, ?, ?, ?)
            """, (company_scoring_id, p["fullName"], str(p["pinfl"]), p["position"], p["privilegeTypeId"]))
             





def save_aid_type(code: int, name: str, last_update : str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO aid_types (id, name, last_update_date) VALUES (?, ?, ?)', 
            (code, name, last_update )
        )
    
def get_aid_type(code: int):
    with conn:
        aid = conn.execute(
            'SELECT name, last_update_date from aid_types where id = ?', 
            (code,)
        ).fetchone()
        return dict(aid)
    
def save_privilege_type(code: int, name: str, last_update : str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO privilege_types (id, name, last_update_date) VALUES (?, ?, ?)', 
            (code, name, last_update )
        )
def get_privilege_type(code: int):
    with conn:
        privilege = conn.execute(
            'SELECT name, last_update_date from privilege_types where id = ?', 
            (code,)
        ).fetchone()
        return dict(privilege)

def save_initiative_type(id: int, code: str, name: str, last_update : str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO initiatives_types (id, code,  name, last_update_date) VALUES (?, ?, ?, ?)', 
            (id, code, name, last_update)
        )
def get_initiative_id_type(id: int):
    with conn:
        initiative = conn.execute(
            'SELECT name, last_update_date from initiatives_types where id = ?', 
            (id,)
        ).fetchone()
        return dict(initiative)

def get_code_type(code: str):
    with conn:
        initiative = conn.execute(
            'SELECT name, last_update_date from initiatives_types where code = ?', 
            (code,)
        ).fetchone()
        return dict(initiative)
    
def save_token(access_token : str, expire_date : str):
    with conn:
        conn.execute(
            'INSERT OR REPLACE INTO token (id, access_token, expire_date) VALUES (1, ?, ?)', 
            (access_token, expire_date)
        )
               
def get_current_token():
    with conn:
        token = conn.execute('SELECT access_token, expire_date FROM token WHERE id = 1').fetchone()
        return dict(token)
 
 
 
 
 
 
 
def get_all_loans() -> list[dict]:
    rows = conn.execute('SELECT * FROM loans').fetchall()
    return [dict(r) for r in rows]

def get_loan_schedule(loan_id: int) -> list[dict]:
    rows = conn.execute(
        'SELECT * FROM loan_schedule WHERE loan_id = ? ORDER BY order_num', (loan_id,)
    ).fetchall()
    return [dict(r) for r in rows]

def get_loan_accounts(loan_id: int) -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_accounts WHERE loan_id = ?', (loan_id,)).fetchall()
    return [dict(r) for r in rows]

def get_all_scorings() -> list[dict]:
    rows = conn.execute('SELECT * FROM scorings').fetchall()
    return [dict(r) for r in rows]
 
def get_all_schedules() -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_schedule').fetchall()
    return [dict(r) for r in rows]

def get_all_accounts() -> list[dict]:
    rows = conn.execute('SELECT * FROM loan_accounts').fetchall()
    return [dict(r) for r in rows]

def get_all_privileges() -> list[dict]:
    rows = conn.execute('SELECT * FROM scoring_privileges').fetchall()
    return [dict(r) for r in rows]