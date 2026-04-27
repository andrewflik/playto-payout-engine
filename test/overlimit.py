'''
    simple sa test ha to not allow debit balance se zyda payout create karne se.
'''
import requests

URL = "http://127.0.0.1:8000/api/v1/payouts/"

def test_insufficient_balance():
    res = requests.post(URL, json={
        "merchant_id": "41916517-558b-445e-b69f-342bb4991963",
        "amount_paise": 99999922999,
        "bank_account_id": "........"
    }, headers={"Idempotency-Key": "fail-test"})

    print(res.status_code, res.json())

    assert res.status_code == 400

if __name__ == "__main__":
    test_insufficient_balance()