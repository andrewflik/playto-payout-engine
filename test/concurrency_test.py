'''
    I'm trying to to test if 10 threads hit the same endpoint with same 
    idempotency key at the same time, will they all get the same payout id in response   

    ALL responses → same id
    1 request → 201
    rest → 200

    Result -> only one payout created, 
    rest got the same payout returned, 
    no errors/exceptions

    Creation pe 201 agya and rest of the rquest as expected 200 return kra with same response.
'''

import requests
import threading

URL = "http://127.0.0.1:8000/api/v1/payouts/"
HEADERS = {
    "Content-Type": "application/json",
    "Idempotency-Key": "concurrency-test"
}
DATA = {
    "merchant_id": "41916517-558b-445e-b69f-342bb4991963",
    "amount_paise": 12,
    "bank_account_id": "........"
}

results = []
errors = []

def hit():
    try:
        res = requests.post(URL, json=DATA, headers=HEADERS)
        results.append(res)
    except Exception as e:
        errors.append(str(e))


def test_concurrency():
    threads = [threading.Thread(target=hit) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # 🔍 debug output
    for r in results:
        print(r.status_code, r.json())

    assert len(errors) == 0

    ids = [r.json()["id"] for r in results if r.status_code in (200, 201)]

    # 🔥 KEY ASSERTION
    assert len(set(ids)) == 1

if __name__ == "__main__":
    test_concurrency()