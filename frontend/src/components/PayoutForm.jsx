import { useState } from 'react'
import { createPayout } from '../api/client'

export default function PayoutForm({ merchantId, onSuccess }) {
  const [amount, setAmount] = useState('')
  const [bankAccount, setBankAccount] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    setError(null)

    // validate
    const amountPaise = Math.round(parseFloat(amount) * 100)
    if (!amount || amountPaise <= 0) {
      setError('Enter a valid amount')
      return
    }
    if (!bankAccount.trim()) {
      setError('Enter a bank account ID')
      return
    }

    setLoading(true)
    try {
      await createPayout(merchantId, amountPaise, bankAccount.trim())
      setAmount('')
      setBankAccount('')
      onSuccess()
    } catch (err) {
      setError(
        err.response?.data?.error || 'Something went wrong'
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <h2 className="text-sm font-medium text-gray-900 mb-4">
        Request payout
      </h2>

      <div className="mb-3">
        <label className="block text-xs text-gray-500 mb-1">
          Amount (₹)
        </label>
        <input
          type="number"
          value={amount}
          onChange={e => setAmount(e.target.value)}
          placeholder="e.g. 1000"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
        />
      </div>

      <div className="mb-4">
        <label className="block text-xs text-gray-500 mb-1">
          Bank account ID
        </label>
        <input
          type="text"
          value={bankAccount}
          onChange={e => setBankAccount(e.target.value)}
          placeholder="e.g. HDFC_001"
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
        />
      </div>

      {error && (
        <p className="text-xs text-red-600 mb-3">{error}</p>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full bg-green-700 text-white rounded-lg py-2 text-sm font-medium disabled:opacity-50"
      >
        {loading ? 'Processing...' : 'Withdraw funds'}
      </button>
    </div>
  )
}