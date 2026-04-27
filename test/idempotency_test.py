'''
    Testong idempotency of payout creation.
    Idea ha ki agar same request multiple times aayi toh bhi ek hi payout create ho, aur baki requests ko existing payout return krna chahiye.

    Res1: 201 → created
    Res2: 200 → returned existing
'''

import requests

URL = "http://127.0.0.1:8000/api/v1/payouts/"
HEADERS = {
    "Content-Type": "application/json",
    "Idempotency-Key": "abc123"
}
DATA = {
    "merchant_id": "41916517-558b-445e-b69f-342bb4991963",
    "amount_paise": 233,
    "bank_account_id": "........"
}

def test_idempotency():
    res1 = requests.post(URL, json=DATA, headers=HEADERS)
    res2 = requests.post(URL, json=DATA, headers=HEADERS)

    print("Res1:", res1.status_code, res1.json())
    print("Res2:", res2.status_code, res2.json())

    assert res1.status_code in (200, 201)
    assert res2.status_code in (200, 201)

    assert res1.json()["id"] == res2.json()["id"]

if __name__ == "__main__":
    test_idempotency()