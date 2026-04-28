import axios from 'axios'

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

export const getBalance = (merchantId) =>
  api.get(`/merchants/${merchantId}/balance/`)

export const getPayouts = (merchantId) =>
  api.get(`/payouts/list/?merchant_id=${merchantId}`)

export const createPayout = (merchantId, amount, bankAccountId) =>
  api.post('/payouts/', {
    merchant_id: merchantId,
    amount_paise: amount,
    bank_account_id: bankAccountId,
  }, {
    headers: {
    // send unique idem key from here
      'Idempotency-Key': crypto.randomUUID()
    }
  })

export const getMerchants = () =>
  api.get('/merchants/')