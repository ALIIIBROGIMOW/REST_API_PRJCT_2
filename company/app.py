
import os
from functools import wraps
from datetime import datetime, date, timedelta
from flask import Flask, render_template, request, jsonify, redirect, current_app
import requests
import hmac
import random
import base64
import json
import db 
import hashlib
import secrets


from dotenv import load_dotenv
load_dotenv()

def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):        
        h = request.headers.get('Authorization', '')
        token = h[7:] if h.startswith('Bearer ') else ''
        if not token:
            return '', 401
        
        db_token = db.get_token(token)
        if db_token is None:
            return '', 401
         
        try:
            expired = date.today() > datetime.strptime(db_token["expire_date"], "%d.%m.%Y").date()
        except Exception:
            return '', 500
        if expired:
            return '', 401
        
        return func(*args, **kwargs)
    return wrapper



app = Flask(__name__)
BANK_URL = os.environ.get('BANK_URL', 'http://localhost:5000')

db.init_db()


@app.route('/')
def index():
    return render_template('index.html',
        aid_types=db.get_aid_types(lang='RU'),
        privilege_types=db.get_privilege_types(lang='RU'),
        initiative_types=db.get_initiative_types(lang='RU'),
        scorings=db.get_all_scorings(),
        dossiers=db.get_alldossiers(),
        operations=db.get_all_operations(),
        loans=db.get_all_loans(),
        schedules = db.get_all_schedules(),
        users=db.get_users_with_tokens(),
        scoring_privileges=db.get_all_scoring_privileges(),
    ) 


@app.post('/api/auth/login-credentials')
def login_credentials():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
    except Exception:
        return '', 400

    try:
        user = db.get_user_by_username(username)
    except Exception:
        return '', 500
    if user is None:
        return '', 401

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    if not hmac.compare_digest(password_hash, user['password_hash']):
        return '', 401

    token = secrets.token_hex(200)
    expire_date = (date.today() + timedelta(days=7)).strftime('%d.%m.%Y')

    try:
        db.add_token(access_token=token, expire_date=expire_date, user_id=user['id'])
    except Exception:
        return '', 500

    return jsonify({'accessToken': token, 'expireDate': expire_date}), 200


@app.get('/api/financial-aid-types')
@require_token
def api_get_aid_types():
    lang = request.headers.get('Accepted-Language', 'RU')
    try:
        aid_types = db.get_aid_types(lang=lang)
    except Exception:
        return '', 500
    return jsonify(aid_types), 200


@app.get('/api/financial-privilege-types')
@require_token
def api_get_privilege_types():
    lang = request.headers.get('Accepted-Language', 'RU')
    try:
        privilege_types = db.get_privilege_types(lang=lang)
    except Exception:
        return '', 500
    return jsonify(privilege_types), 200


@app.get('/api/financial-initiative-types')
@require_token
def api_get_initiative_types():
    lang = request.headers.get('Accepted-Language', 'RU')
    try:
        initiative_types = db.get_initiative_types(lang=lang)
    except Exception:
        return '', 500
    return jsonify(initiative_types), 200



def run_scoring(katm_data: dict, tin: str, description: str | None) -> tuple[str, int]:
    # Заглушка — детерминированная логика по сумме цифр ИНН:
    # чётная → AGREE, нечётная → DISAGREE.
    # Категория региона — остаток от деления суммы цифр на 4, плюс 1 (диапазон 1–4).
    # TODO: заменить на реальный алгоритм после уточнения у куратора.
    digit_sum = sum(int(d) for d in str(tin) if d.isdigit())
    result = 'AGREE' if digit_sum % 2 == 0 else 'DISAGREE'
    category = (digit_sum % 4) + 1
    return result, category

def run_guarantee_scoring(
    katm_data: dict,
    tin: str,
    loan_amount: int,
    guarantee_amount: int,
    guarantee_period: int,
) -> tuple[str, int]:
    # Заглушка — детерминированная логика:
    # guarantee_amount не должна превышать 50% от loan_amount
    # и сумма цифр ИНН чётная → AGREE, иначе DISAGREE.
    # TODO: заменить на реальный алгоритм после уточнения у куратора.
    digit_sum = sum(int(d) for d in str(tin) if d.isdigit())
    if guarantee_amount > loan_amount * 0.5 or digit_sum % 2 != 0:
        result = 'DISAGREE'
    else:
        result = 'AGREE'
    category = (digit_sum % 4) + 1
    return result, category






@app.post('/api/scoring-GUARANTEE')
@require_token
def api_start_scoring_guarantee():
    data = request.get_json(silent=True)
    if data is None:
        return '', 400

    tin : int = data.get('tin')
    application_number : str = data.get('applicationNumber')
    financial_aid_type : str = data.get('financialAidType')
    initiative_id : int | None = data.get('initiativeId')
    loan_amount : int       = data.get('loanAmount')
    guarantee_amount : int  = data.get('guaranteeAmount')
    guarantee_period : int  = data.get('guaranteePeriod')
    katm_base64 : str        = data.get('katmBase64')

    if any(v is None for v in [tin, application_number, financial_aid_type, loan_amount, guarantee_amount, guarantee_period, katm_base64]):
        return '', 400

    try:
        katm_data = json.loads(base64.b64decode(katm_base64).decode())
    except Exception:
        return '', 400
    try:
        scoring_id = db.create_scoring(
            tin                = str(tin),
            scoring_type       = 'GUARANTEE',
            application_number = str(application_number),
            katm_data          = json.dumps(katm_data),
            financial_aid_type = int(financial_aid_type),
            initiative_id      = int(initiative_id) if initiative_id is not None else None,
            loan_amount        = int(loan_amount),
            guarantee_amount   = int(guarantee_amount),
            guarantee_period   = int(guarantee_period),
        )

        result, category = run_guarantee_scoring(
            katm_data        = katm_data,
            tin              = str(tin),
            loan_amount      = int(loan_amount),
            guarantee_amount = int(guarantee_amount),
            guarantee_period = int(guarantee_period),
        )
        
        report_path = f'/reports/guarantee_{scoring_id}.pdf'   # заглушка пути

        db.save_scoring_result(
            scoring_id  = scoring_id,
            result      = result,
            category    = category,
            report_path = report_path,
        )
    except (ValueError, TypeError):
        return '', 400
    except Exception:
        return '', 500
    return jsonify({'id': scoring_id}), 200 


@app.post('/api/scoring-PF-312')
@require_token
def api_start_scoring_pf312():
    data = request.get_json(silent=True)
    if data is None:
        return '', 400

    tin : int                = data.get('tin')
    application_number : str = data.get('applicationNumber')
    description : str        = data.get('description')
    katm_base64 : str        = data.get('katmBase64')

    if not tin or not application_number or not katm_base64:
        return '', 400

    try:
        katm_data = json.loads(base64.b64decode(katm_base64).decode())
    except Exception:
        return '', 400

    try:
        scoring_id = db.create_scoring(
            scoring_type       = 'PF-312',
            tin                = str(tin),
            application_number = str(application_number),
            katm_data          = json.dumps(katm_data),
            description        = description,
        )

        result, category = run_scoring(katm_data, str(tin), description)
        report_path = f'/reports/{scoring_id}.pdf'  # заглушка пути

        db.save_scoring_result(
            scoring_id  = scoring_id,
            result      = result,
            category    = category,
            report_path = report_path,
        )
    except Exception:
            return '', 500

    return jsonify({'id': scoring_id}), 200


@app.get('/api/scoring/<int:scoring_id>/result')
@require_token
def api_get_scoring_result(scoring_id: int):
    tin                = request.args.get('tin')
    application_number = request.args.get('applicationNumber')

    if not tin and not application_number:
        return '', 400

    try:
        scoring = db.get_scoring(scoring_id)
    except Exception:
        return '', 500
    
    if scoring is None:
        return '', 404

    if scoring['status'] == 'PENDING':
        return jsonify({'status': 'PENDING'}), 200

    try:
        privileges_raw = db.get_scoring_privileges(scoring_id)
    except Exception:
        return '', 500
    privileges = [
        {
            'fullName':        p['full_name'],
            'pinfl':           p['pinfl'],
            'position':        p['position'],
            'privilegeTypeId': p['privilege_type_id'],
        }
        for p in privileges_raw
    ]

    return jsonify({
        'category':    scoring['category'],  # по ТЗ именно sategory - здесь исправили.
        'result':      scoring['result'],
        'responseLink': scoring['report_path'],
        'privileges':  privileges,
    }), 200
     
    
def generate_grk_id() -> str:
    # В реале приходит от ЦБ. В прототипе — случайное 18-значное число.
    return str(random.randint(100000000000000000, 999999999999999999))


@app.post('/api/notify-loan')
@require_token
def api_notify_loan():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    items : list = data.get('data')
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    result = []

    for item in items:
        tin    : int            = item.get('tin')
        claim_id    : int       = item.get('claim_id')
        application_number : int = item.get('application_number')

        if not tin or not claim_id:
            return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

        # Проверяем что скоринг существует и одобрен
        try:
            scoring = db.get_scoring(int(claim_id))
        except Exception:
            return jsonify({'result_code': 500, 'is_success': "false", 'message': 'Internal Server Error', 'data': None}), 500
        if scoring is None:
            return jsonify({'result_code': 499, 'is_success': "false", 'message': 'Ne naydeno', 'data': None}), 404
        if scoring['result'] != 'AGREE':
            return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

        try:
            # Проверяем что кредит по этой заявке ещё не создан
            existing = db.get_loan_by_claim_id(int(claim_id))
            if existing is not None:
                # кредит уже зарегистрирован — возвращаем существующие данные
                result.append({
                    'loan_id':            existing['id'],
                    'grk_id':             existing['grk_id'],
                    'tin':                existing['tin'],
                    'claim_id':           existing['claim_id'],
                    'application_number': existing['application_number'],
                })
                continue

            grk_id  = generate_grk_id()
            loan_id = db.create_loan(
                tin                = str(tin),
                claim_id           = int(claim_id),
                application_number = str(application_number),
                grk_id             = grk_id,
            )
        except Exception:
            return jsonify({'result_code': 500, 'is_success': "false", 'message': 'Internal Server Error', 'data': None}), 500

        result.append({
            'loan_id':            loan_id,
            'grk_id':             grk_id,
            'tin':                str(tin),
            'claim_id':           int(claim_id),
            'application_number': str(application_number),
        })

    return jsonify({'result_code': 1, 'is_success': 'true',
                    'message': 'Operation completed successfully',
                    'data': result}), 200
    
    
    
    
# Метод 6 — досье по кредиту
@app.post('/api/loan-dossier')
@require_token
def api_loan_dossier():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    items: list = data.get('data')
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    result = []
    for item in items:
        loan_id = item.get('loan_id')
        if loan_id is None:
            return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400


        try:
            dossier = db.get_loan_dossier(int(loan_id))
        except Exception:
            return jsonify({'result_code': 500, 'is_success': "false", 'message': 'Internal Server Error', 'data': None}), 500
        if dossier is None:
            return jsonify({'result_code': 499, 'is_success': "false", 'message': 'Ne naydeno', 'data': None}), 404

        result.append({
            'loan_id':                    loan_id,
            'branch_code':                dossier['branch_code'],
            'head_bank_code':             dossier['head_bank_code'],
            'client_name':                dossier['client_name'],
            'client_type_code':           dossier['client_type_code'],
            'oked':                       dossier['oked'],
            'currency_code':              dossier['currency_code'],
            'loan_type_code':             dossier['loan_type_code'],
            'loan_collateral_type':       dossier['loan_collateral_type'],
            'purpose_code':               dossier['purpose_code'],
            'purpose_subcode':            dossier['purpose_subcode'],
            'agreement_date':             dossier['agreement_date'],
            'actual_date':                dossier['actual_date'],
            'repayment_dead_line':        dossier['repayment_deadline'],
            'loan_amount':                dossier['loan_amount'],
            'actually_disbursed_amount':  dossier['actually_disbursed_amount'],
            'rate':                       dossier['rate'],
            'source_lending':             dossier['source_lending'],
            'source_lending_type':        dossier['source_lending_type'],
            'credit_status':              dossier['credit_status'],
            'classification_code':        dossier['classification_code'],
            'principal_debt_past_days':   dossier['principal_debt_past_days'],
            'interest_past_days':         dossier['interest_past_days'],
            'legal_act_code':             dossier['legal_act_code'],
            'loan_grace_period':          dossier['loan_grace_period'],
        })

    return jsonify({'result_code': 1, 'is_success': 'true',
                    'message': 'Operation completed successfully',
                    'data': result}), 200


# Метод 7 — график погашения
@app.post('/api/loan-schedule')
@require_token
def api_loan_schedule():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    loan_id = data.get('loan_id')
    if loan_id is None:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    try:
        schedule = db.get_loan_schedule(int(loan_id))
    except Exception:
        return jsonify({'result_code': 500, 'is_success': "false", 'message': 'Internal Server Error', 'data': None}), 500
    if not schedule:
        return jsonify({'result_code': 499, 'is_success': "false", 'message': 'Ne naydeno', 'data': None}), 404


    payments = [
        {
            'order_num':            p['order_num'],
            'return_date':          p['return_date'],
            'principal_debt':       p['principal_debt'],
            'percentage_amount':    p['percentage_amount'],
            'payable_total_amount': p['payable_total_amount'],
            'principal_balance':    p['principal_balance'],
            'days_in_month':        p['days_in_month'],
        }
        for p in schedule
    ]

    return jsonify({'result_code': 1, 'is_success': 'true',
                    'message': 'Operation completed successfully',
                    'data': payments}), 200



# Метод 8 — обороты по счетам
@app.post('/api/loan-accounts')
@require_token
def api_loan_accounts():
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400

    loan_id      = data.get('loan_id')
    period_start = data.get('period_start')
    period_end   = data.get('period_end')

    if not loan_id or not period_start or not period_end:
        return jsonify({'result_code': 400, 'is_success': "false", 'message': 'Bad Request', 'data': None}), 400


    try:
        accounts = get_loan_accounts(int(loan_id), period_start, period_end)
    except Exception:
        return jsonify({'result_code': 500, 'is_success': "false", 'message': 'Internal Server Error', 'data': None}), 500
    if not accounts:
        return jsonify({'result_code': 499, 'is_success': "false", 'message': 'Ne naydeno', 'data': None}), 404

    result = [
        {
            'account':              a['account'],
            'account_type':         a['account_type'],
            'ostatok_period_start': a['balance_start'],
            'ostatok_period_end':   a['balance_end'],
            'oborot':               a['operations'],
        }
        for a in accounts
    ]

    return jsonify({'result_code': 1, 'is_success': 'true',
                    'message': 'Operation completed successfully',
                    'data': result}), 200



def _date_out_of_iso(date_str: str) -> str:
    year, month, day = date_str.split('-')
    return f'{year}.{month}.{day}'

def get_loan_accounts(loan_id, period_start, period_end):
    ops = db.get_loan_operations(loan_id, period_start, period_end)
    
    # группируем по счёту
    accounts = {}    
    balance_start = 0 # заглушка - в продукте берется из остатка.
    for op in ops:
        acc = op['account']
        if acc not in accounts:
            accounts[acc] = {
                'account':       acc,
                'account_type':  op['account_type'],
                'balance_start': balance_start,
                'operations':    []
            }
        accounts[acc]['operations'].append({
            'debit':          op['debit'],
            'credit':         op['credit'],
            'operation_date': _date_out_of_iso(op['operation_date']),
        })
    
    # считаем balance_end
    for acc in accounts.values():
        total_debit  = sum(o['debit']  for o in acc['operations'])
        total_credit = sum(o['credit'] for o in acc['operations'])
        acc['balance_end'] = balance_start + total_debit - total_credit
    
    return list(accounts.values())



if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5001)))
