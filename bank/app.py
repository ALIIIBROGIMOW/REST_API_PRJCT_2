#TODO - сделать копию проекта где не "как по ТЗ" а как надо. чтобы не было str vs num в кодах и противоречеше 

import os
from functools import wraps
from datetime import datetime, date
from flask import Flask, render_template, request, jsonify, redirect, current_app
import requests
import hmac
import base64
import json
import db 


from dotenv import load_dotenv
load_dotenv()

BANK_LOGIN = os.environ.get('BANK_LOGIN', 'test_bank')
BANK_PASSWORD = os.environ.get('BANK_PASSWORD', '5959-c2b1-66OfDavmJmM6-62')

LANG = os.environ.get("LANG", 'RU')
 
app = Flask(__name__)
COMPANY_URL = os.environ.get('COMPANY_URL', 'http://localhost:5001')

db.init_db()          # создать таблицы при старте
# jsonify необязателен для dict и list, но лучше задавать явно.
 

@app.route('/')
def index():
    try:
        token = db.get_current_token()
    except Exception:
        token = None

    return render_template('index.html',
        login=BANK_LOGIN,
        token=token,
        aid_types=db.get_all_aid_types(),
        privilege_types=db.get_all_privilege_types(),
        initiative_types=db.get_all_initiative_types(),
        scorings=db.get_all_scorings(),
        loans=db.get_all_loans(),
        schedules=db.get_all_schedules(),
        accounts=db.get_all_accounts(),
        privileges=db.get_all_privileges(),
    )


@app.post('/force_refresh_token')# для демонстрационного интерфейса   
def force_token_manually():   
    take_actual_token(force = True)
    return redirect('/')

def take_actual_token(force=False):
    if force:
        new_data = fetch_token()
        return new_data
    data = db.get_current_token()
    expire_date = datetime.strptime(data["expire_date"], "%d.%m.%Y").date()
    if date.today() > expire_date:
        new_data = fetch_token()
        return new_data
    else:
        return data    
    

def fetch_token() -> dict:#TODO - сделать обработку ошибок
    payload = {
        'username': BANK_LOGIN,
        'password': BANK_PASSWORD
    }
    try:
        result = requests.post(f'{COMPANY_URL}/api/auth/login-credentials', json=payload, timeout=10)
    except requests.RequestException as e:
        raise RuntimeError(f"Company unreachable: {e}")
    # DD.MM.YYYY - гарантируется компанией
    if result.status_code != 200:
        raise RuntimeError(f"Login failed, company returned {result.status_code}")
    token_data = result.json()
    parsed_token = {
        "access_token": token_data["accessToken"],
        "expire_date" : token_data["expireDate"]
    }
    db.save_token(parsed_token["access_token"], parsed_token["expire_date"])
    return parsed_token
    
    

take_actual_token(force = True)
    

    
@app.post('/request-aid-types')
def request_aid_types():
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    try:
        result = requests.get(
            f'{COMPANY_URL}/api/financial-aid-types',
            headers={'Authorization': f'Bearer {token}', 'Accepted-Language': LANG},
            timeout=10
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    
    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе видов помощи: HTTP {result.status_code}', 502


    data = result.json()
    last_update_date = datetime.now().strftime("%d.%m.%Y")
    
    for item in data:
        db.save_aid_type(
            code=item.get('id'),
            name=item.get('name'),
            last_update=last_update_date
        )
    return redirect('/')


    
@app.post('/request-privilege-types')
def request_privilege_types():
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    try:
        result = requests.get(
            f'{COMPANY_URL}/api/financial-privilege-types', 
            headers={
                'Authorization': f'Bearer {token}',
                'Accepted-Language': LANG
            }, 
            timeout=10
        )    
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе видов льгот: HTTP {result.status_code}', 502

    data = result.json()
    last_update_date = datetime.now().strftime("%d.%m.%Y")
    
    for item in data:
        db.save_privilege_type(
            code=item.get('id'),
            name=item.get('name'),
            last_update=last_update_date
        )
    return redirect('/')




@app.post('/request-initiative-types')# В ТЗ оба API идентичны с API of aid
def request_initiative_types():
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    
    try:
        result = requests.get(
            f'{COMPANY_URL}/api/financial-initiative-types', 
            headers={
                'Authorization': f'Bearer {token}',
                'Accepted-Language': LANG
            }, 
            timeout=10
        )  
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502

    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе видов инициатив: HTTP {result.status_code}', 502


    data = result.json()
    last_update_date = datetime.now().strftime("%d.%m.%Y")
    
    for item in data:
        db.save_initiative_type(
            id=item.get('id'),
            code=item.get('code'),            
            name=item.get('name'),
            last_update=last_update_date
        )
    return redirect('/')



katm_fake_data = {
    "31201995550018": {
        "active_loans": 2,
        "overdue_days": 0,
        "total_debt": 5000000,
        "monthly_income": 3000000
    },
    "38496685078981": {
        "active_loans": 0,
        "overdue_days": 0,
        "total_debt": 0,
        "monthly_income": 8500000
    },
    "50412984440021": {
        "active_loans": 4,
        "overdue_days": 45,
        "total_debt": 32000000,
        "monthly_income": 4200000
    },
    "62305771920043": {
        "active_loans": 1,
        "overdue_days": 7,
        "total_debt": 12500000,
        "monthly_income": 6000000
    },
    "47819203650077": {
        "active_loans": 3,
        "overdue_days": 0,
        "total_debt": 18700000,
        "monthly_income": 11000000
    }
}


def get_katm_report(tin : int|str):
    # ПРОТОТИП: формируем из введённых данных
    report = katm_fake_data[str(tin)]
    # в реальности - нужно делать запрос в КАТМ по tin 
    result = base64.b64encode(json.dumps(report).encode()).decode()
    return result


@app.post('/start-scoring-PF-312') 
def start_scoring_PF_312():
    tin_payload: int = int(request.form.get('tin', 11111111111111))
    is_work_payload : str = request.form.get('is_work', "no")
    application_number_payload : str = request.form.get('application_number', "111111111111111")
    
    
    
    try:
        base64_file_payload: str = get_katm_report(tin_payload)
    except KeyError:
        return f'В тестовых данных КАТМ нет записи для ИНН {tin_payload}', 400

    
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    
    payload = {
        "tin": tin_payload,
        "description": is_work_payload,
        "applicationNumber": application_number_payload,
        "katmBase64": base64_file_payload
    }
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/scoring-PF-312",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )

    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502

    if result.status_code != 200:
        return f'Компания отклонила скоринг PF-312: HTTP {result.status_code}', 502

        

    data = result.json()   
    try:
        db.create_scoring(company_scoring_id=int(data["id"]),
                        scoring_type = "PF-312",
                        application_number=application_number_payload,
                        tin=str(tin_payload))
    except Exception as e:
        return f'Скоринг создан в компании (id={data.get("id")}), но не сохранён локально: {e}', 500

    return redirect('/')





@app.post('/start-scoring-GUARANTEE') 
def start_scoring_GUARANTEE():
    tin_payload: int = int(request.form.get('tin', 11111111111111))
    application_number_payload : str = request.form.get('application_number', "111111111111111")
    financial_aid_type_payload : str = request.form.get('financial_aid_type', "000") #TODO - в HTML будет выпадающий список из НАЗВАНИЙ, который должен передовать КОДЫ. И то и то берется из таблицы. Нужно решить гле обрабатывать названия -> коды, тут или в index.html
    initiative_type_middle_res = request.form.get('initiative_type', None) #TODO - в HTML будет выпадающий список из НАЗВАНИЙ, который должен передовать КОДЫ. И то и то берется из таблицы. Нужно решить гле обрабатывать названия -> коды, тут или в index.html
    initiative_type_payload : int | None
    if initiative_type_middle_res is not None:
        try:
            initiative_type_payload = int(initiative_type_middle_res)
        except ValueError:
            return f'Некорректный код инициативы: {initiative_type_middle_res}', 400
    else:
        initiative_type_payload = None # логика int vs str в отношении кодов и tin/ПИНФЛ и id в ТЗ - это отдельный вид искуства...
        
        
    try:
        loan_amount_payload : int = int(request.form.get('loan_amount', 0))
        guarantee_amount_payload : int = int(request.form.get('guarantee_amount', 0))
        guarantee_period_payload : int = int(request.form.get('guarantee_period', 0))
    except ValueError:
        return 'Сумма кредита, сумма гарантии и срок гарантии должны быть числами', 400

    try:
        base64_file_payload: str = get_katm_report(tin_payload)
    except KeyError:
        return f'В тестовых данных КАТМ нет записи для ИНН {tin_payload}', 400
    
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    
    payload = {
        "tin": tin_payload,
        "applicationNumber" : application_number_payload,
        "financialAidType" : financial_aid_type_payload,
        "initiativeId" : initiative_type_payload,
        "loanAmount" : loan_amount_payload,
        "guaranteeAmount" : guarantee_amount_payload,
        "guaranteePeriod" : guarantee_period_payload,
        "katmBase64": base64_file_payload
    }
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/scoring-GUARANTEE",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    if result.status_code != 200:
        return f'Компания отклонила скоринг GUARANTEE: HTTP {result.status_code}', 502


    data = result.json()   
    try:
        db.create_scoring(company_scoring_id=int(data["id"]),
                        scoring_type = "GUARANTEE",
                        application_number=application_number_payload,
                        tin=str(tin_payload))
    except Exception as e:
        return f'Скоринг создан в компании (id={data.get("id")}), но не сохранён локально: {e}', 500

    return redirect('/')
  

@app.post('/manual_check_scoring') # для демонстрационного интерфейса - на практике используется поллинг
def manual_check_scoring():
    tin_for_get: int = int(request.form.get('tin', 11111111111111))
    company_scoring_id_for_get : int = int(request.form.get('company_scoring_id', 0))
    application_number_for_get : str = request.form.get('application_number', "111111111111111") 

    error = check_scoring(
        company_scoring_id=company_scoring_id_for_get,
        application_number=application_number_for_get,
        tin=tin_for_get
    )
    if error is not None:
        message, status = error
        return message, status
    return redirect('/')
    
def check_scoring(company_scoring_id : int, application_number : str, tin : int):  
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    try:
        response = requests.get(
            f"{COMPANY_URL}/api/scoring/{company_scoring_id}/result",
            params={
                "applicationNumber": application_number,
                "tin": tin
            },
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502

    if response.status_code == 404:
        return f'Скоринг {company_scoring_id} не найден в компании', 404
    if response.status_code != 200:
        return f'Компания вернула ошибку при проверке скоринга: HTTP {response.status_code}', 502



    data = response.json() 
    
    if data.get('status') == 'PENDING':
        return 'Скоринг еще не готов (PENDING), попробуйте позже', 202

    try:
        company_scoring_id_for_db : int = int(company_scoring_id)
        
        db.save_scoring_result(
            company_scoring_id = company_scoring_id_for_db,
            category = data["category"], # по ТЗ - sategory - здесь исправили.
            result = data["result"],
            response_link = data["responseLink"],  
        )
        privileges_for_db : list = data["privileges"]
        
        db.save_privileges(company_scoring_id=company_scoring_id_for_db, privileges=privileges_for_db)
    except KeyError as e:
        return f'Компания вернула неполные данные по скорингу, отсутствует поле {e}', 502
    except Exception as e:
        return f'Не удалось сохранить результат скоринга локально: {e}', 500

    return None
    
    


@app.post('/manual_send_loan_data') # для демонстрационного интерфейса - на практике отправляет периодически/при создании кредита
def manual_send_loan_data():
    # в HTML - таблица со скорингами, каждая с галочкой, при нажатии кнопки "выдать" - срабатывает.
    # форма передаёт несколько значений с одним именем - getlist возвращает список
    #<input type="checkbox" name="company_scoring_id" value="{{ scoring.company_scoring_id }}">
    raw = request.form.getlist('company_scoring_id')
    try:
        ids = [int(x) for x in raw]
    except ValueError:
        return 'Некорректный id скоринга в форме', 400
    error = send_loan_data(company_scoring_ids=ids)
    if error is not None:
        message, status = error
        return message, status
    return redirect('/')

    
# в прототипе - вызывать вручную.
def send_loan_data(company_scoring_ids : list[int]): #Принимает список id заявок/сокрингов, по которым были оформлены кредиты и создает по ним кредиты используя данные от компании. Также уведомляет компанию.
    try:
        token = take_actual_token()["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500
    
    
    payload = {
        "data" : []
    }    
    try:
        for id in company_scoring_ids:
            scoring = db.get_scoring_by_company_id(company_scoring_id=id)
            payload["data"].append({# отлично, теперь придется разбираться с тем чтобы application_number была допустипа к int, потому что в ЭТОМ запросе решили что передаем int. а ОБРАТНО получаем string. Гении...
                    "tin":  int(scoring["tin"]), # и tin...
                    "claim_id": scoring["company_scoring_id"],
                    "application_number": int(scoring["application_number"]) 
            })
    except Exception as e:
        return f'Не удалось собрать данные по скорингам для отправки: {e}', 500

        
        
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/notify-loan",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    
    if result.status_code != 200:
        return f'Компания отклонила выдачу кредита: HTTP {result.status_code}', 502

    body = result.json()
    result_code = body.get('result_code')
    
    if result_code != 1:
        return f'Компания вернула ошибку выдачи кредита, result_code={result_code}, message={body.get("message")}', 400

    
    
    try:
        data : list = body["data"]     
        for loan in data:
            db.create_loan(
                company_scoring_id = loan["claim_id"],
                tin = loan["tin"],
                application_number = loan["application_number"], 
                company_loan_id = loan["loan_id"],
                grk_id = loan["grk_id"]
                )
    except Exception as e:
        return f'Кредит создан в компании, но не сохранён локально: {e}', 500

    return None

@app.post('/manual_get_loan_dossiers') # для демонстрационного интерфейса - на практике отправляет периодически/при создании кредита
def manual_get_loan_dossiers():
    # в HTML - таблица со скорингами, каждая с галочкой, при нажатии кнопки "выдать" - срабатывает.
    # форма передаёт несколько значений с одним именем - getlist возвращает список
    #<input type="checkbox" name="company_loan_id" value="{{ scoring.company_loan_id }}">
    raw = request.form.getlist('company_loan_id')
    try:
        ids = [int(x) for x in raw]
    except ValueError:
        return 'Некорректный id кредита в форме', 400

    error = get_loan_dossiers(company_loan_ids=ids)
    if error is not None:
        message, status = error
        return message, status
    return redirect('/')
 
      
def get_loan_dossiers(company_loan_ids : list[int]): #Принимает список id кредитов, по которым нужно получить данные и записывает их.
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500 #TODO добавить обработку исключений и незакончиных скорингов
    
    payload = {
        "data" : []
    }
    
    for id in company_loan_ids:
        payload["data"].append({ 
                "loan_id":  id  
            }) 
        
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/loan-dossier",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    
    if result.status_code == 404:
        return 'Один или несколько кредитов не найдены в компании', 404
    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе досье: HTTP {result.status_code}', 502

    body = result.json()
    result_code = body.get('result_code')

    if result_code != 1:
        return f'Компания вернула ошибку выдачи досье, result_code={result_code}, message={body.get("message")}', 400
    try:
        data : list = body["data"] 
        for loan in data:
            db.add_loan_dossier(
                company_loan_id           = loan["loan_id"],
                branch_code               = loan["branch_code"],
                head_bank_code            = loan["head_bank_code"],
                client_name               = loan["client_name"],
                client_type_code          = loan["client_type_code"],
                oked                      = loan["oked"],
                currency_code             = loan["currency_code"],
                loan_type_code            = loan["loan_type_code"],
                loan_collateral_type      = loan["loan_collateral_type"],
                purpose_code              = loan["purpose_code"],
                purpose_subcode           = loan["purpose_subcode"],
                agreement_date            = loan["agreement_date"],
                actual_date               = loan["actual_date"],
                repayment_deadline        = loan["repayment_dead_line"],
                loan_amount               = loan["loan_amount"],
                actually_disbursed_amount = loan["actually_disbursed_amount"],
                rate                      = loan["rate"],
                source_lending            = loan["source_lending"],
                source_lending_type       = loan["source_lending_type"],
                credit_status             = loan["credit_status"],
                classification_code       = loan["classification_code"],
                principal_debt_past_days  = loan["principal_debt_past_days"],
                interest_past_days        = loan["interest_past_days"],
                legal_act_code            = loan["legal_act_code"],
                loan_grace_period         = loan["loan_grace_period"]
            )       
    except KeyError as e:
        return f'Компания вернула неполные данные досье, отсутствует поле {e}', 502
    except Exception as e:
        return f'Не удалось сохранить досье локально: {e}', 500
    return None
    
@app.post('/manual_get_loan_schedule')
def manual_get_loan_schedule():
    try:
        loan_id = int(request.form.get('company_loan_id', 0))#В HTML наверное стоит сделать выпадающий список... или может таблицу с кнопками "запросить X". Это и других записей касается...
    except ValueError:
        return 'Некорректный id кредита в форме', 400

    error = get_loan_schedule(loan_id)
    if error is not None:
        message, status = error
        return message, status
    return redirect('/')
 
 
def get_loan_schedule(loan_id : int): 
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500 
    payload = {
        "loan_id" : loan_id
    } 
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/loan-schedule",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502
    
    if result.status_code == 404:
        return f'График погашения для кредита {loan_id} не найден', 404
    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе графика: HTTP {result.status_code}', 502
    body = result.json()
    result_code = body.get('result_code')
    if result_code != 1:
        return f'Компания вернула ошибку при запросе графика, result_code={result_code}, message={body.get("message")}', 400

    try:
        data: list = body["data"]
        for payment in data:
            db.create_loan_schedule(
                loan_id              = loan_id,
                order_num            = payment["order_num"],
                return_date          = payment["return_date"],
                principal_debt       = payment["principal_debt"],
                percentage_amount    = payment["percentage_amount"],
                payable_total_amount = payment["payable_total_amount"],
                principal_balance    = payment["principal_balance"],
                days_in_month        = payment["days_in_month"]
            )
    except KeyError as e:
        return f'Компания вернула неполные данные графика, отсутствует поле {e}', 502
    except Exception as e:
        return f'Не удалось сохранить график локально: {e}', 500

    return None
        
        
@app.post('/manual_get_loan_accounts')  
def manual_get_loan_accounts():
    
    try:
        loan_id = int(request.form.get('company_loan_id', 0))#В HTML наверное стоит сделать выпадающий список... или может таблицу с кнопками "запросить X". Это и других записей касается...
    except ValueError:
        return 'Некорректный id кредита в форме', 400 
 
    #Можно сделать выпадающий календарь в HTML. И подумать над форматированием, чтобы возвращало DD.MM.YYYY
    period_start = request.form.get('period_start', "01.01.2000") 
    period_end = request.form.get('period_end', "01.01.2001") 
   
    error = get_loan_accounts(loan_id_payload=loan_id, period_start_payload=period_start, period_end_payload=period_end)
    if error is not None:
        message, status = error
        return message, status
    return redirect('/')

         
        
def get_loan_accounts(loan_id_payload : int, period_start_payload : str, period_end_payload : str): 
    try:
        token = take_actual_token(force=False)["access_token"]
    except Exception as e:
        return f'Не удалось получить токен: {e}', 500 
    payload = {
        "loan_id" : loan_id_payload,
        "period_start" : period_start_payload,
        "period_end" : period_end_payload
    } 
    try:
        result = requests.post(
            f"{COMPANY_URL}/api/loan-accounts",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
    except requests.RequestException as e:
        return f'Компания недоступна: {e}', 502

    if result.status_code == 404:
        return f'Обороты по счетам для кредита {loan_id_payload} не найдены за указанный период', 404
    if result.status_code != 200:
        return f'Компания вернула ошибку при запросе оборотов: HTTP {result.status_code}', 502

    body = result.json()
    result_code = body.get('result_code')
    if result_code != 1:
        return f'Компания вернула ошибку при запросе оборотов, result_code={result_code}, message={body.get("message")}', 400

    try:
        data: list = body["data"]
        for account in data:
            db.create_loan_account(
                loan_id = loan_id_payload,
                period_start = period_start_payload,
                period_end = period_end_payload,
                account = account["account"],
                account_type = account["account_type"],
                balance_start = account["ostatok_period_start"],
                balance_end = account["ostatok_period_end"],
                operations = json.dumps(account["oborot"])
            )
    except KeyError as e:
        return f'Компания вернула неполные данные оборотов, отсутствует поле {e}', 502
    except Exception as e:
        return f'Не удалось сохранить обороты локально: {e}', 500

    return None


if __name__ == '__main__':
    app.run(port=int(os.environ.get('PORT', 5000)))