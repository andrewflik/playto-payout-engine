import { useEffect, useState } from 'react'
import { getPayouts } from '../api/client'

const STATUS_STYLES = {
  pending:    'bg-amber-50 text-amber-700',
  processing: 'bg-blue-50 text-blue-700',
  completed:  'bg-green-50 text-green-700',
  failed:     'bg-red-50 text-red-700',
}

const fmt = (paise) => `₹${(paise / 100).toLocaleString('en-IN')}`

const fmtDate = (iso) => new Date(iso).toLocaleString('en-IN', {
  day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit'
})

export default function PayoutHistory({ merchantId, refreshTrigger }) {
  const [payouts, setPayouts] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchPayouts = async () => {
    try {
      const res = await getPayouts(merchantId)
      setPayouts(res.data)
    } catch (err) {
      console.error('Failed to fetch payouts', err)
    } finally {
      setLoading(false)
    }
  }


  useEffect(() => {
    fetchPayouts()
  }, [merchantId, refreshTrigger])

  // poll every 3 seconds
  useEffect(() => {
    const interval = setInterval(fetchPayouts, 3000)
    return () => clearInterval(interval)
  }, [merchantId])

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
        <h2 className="text-sm font-medium text-gray-900">
          Payout history
        </h2>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1,2,3].map(i => (
            <div key={i} className="h-10 bg-gray-100 rounded animate-pulse"/>
          ))}
        </div>
      ) : payouts.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-8">
          No payouts yet
        </p>
      ) : (
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left text-gray-400 font-medium pb-2 uppercase tracking-wide">Amount</th>
              <th className="text-left text-gray-400 font-medium pb-2 uppercase tracking-wide">Bank</th>
              <th className="text-left text-gray-400 font-medium pb-2 uppercase tracking-wide">Status</th>
              <th className="text-left text-gray-400 font-medium pb-2 uppercase tracking-wide">Date</th>
            </tr>
          </thead>
          <tbody>
            {payouts.map(p => (
              <tr key={p.id} className="border-b border-gray-50 last:border-0">
                <td className="py-2 text-red-600 font-medium">
                  −{fmt(p.amount_paise)}
                </td>
                <td className="py-2 text-gray-600">{p.bank_account_id}</td>
                <td className="py-2">
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[p.status]}`}>
                    {p.status}
                  </span>
                </td>
                <td className="py-2 text-gray-400">{fmtDate(p.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}