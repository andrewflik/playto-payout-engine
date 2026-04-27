'''
    Same idempotency key → same response milega.
    first requet jo bhi ayga process hojyga, after that agar same key se request aayi toh existing payout return hojyga
'''
import requests

URL = "http://127.0.0.1:8000/api/v1/payouts/"

def test_same_key_different_amount():
    headers = {"Idempotency-Key": "same-key"}

    res1 = requests.post(URL, json={
        "merchant_id": "41916517-558b-445e-b69f-342bb4991963",
        "amount_paise": 100,
        "bank_account_id": "dD"
    }, headers=headers)

    res2 = requests.post(URL, json={
        "merchant_id": "41916517-558b-445e-b69f-342bb4991963",
        "amount_paise": 999,
        "bank_account_id": "SD"
    }, headers=headers)

    print(res1.json(), res2.json())

    assert res1.json()["id"] == res2.json()["id"]

if __name__ == "__main__":
    test_same_key_different_amount()