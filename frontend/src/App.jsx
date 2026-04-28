import { useState, useEffect, useCallback } from 'react'
import { getMerchants, getBalance } from './api/client'
import BalanceCards from './components/BalanceCards'
import PayoutForm from './components/PayoutForm'
import PayoutHistory from './components/PayoutHistory'

export default function App() {
  const [merchants, setMerchants] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [balance, setBalance] = useState(null)
  const [balanceLoading, setBalanceLoading] = useState(false)
  const [refreshTrigger, setRefreshTrigger] = useState(0)

  useEffect(() => {
    getMerchants().then(res => {
      const merchantsData = Array.isArray(res.data) ? res.data : []
      setMerchants(merchantsData)
      if (merchantsData.length > 0) setSelectedId(merchantsData[0].id)
    })
  }, [])

  // load balance when merchant changes
  useEffect(() => {
    if (!selectedId) return
    setBalanceLoading(true)
    getBalance(selectedId)
      .then(res => setBalance(res.data))
      .finally(() => setBalanceLoading(false))
  }, [selectedId, refreshTrigger])

  const handlePayoutSuccess = useCallback(() => {
    setRefreshTrigger(t => t + 1)
  }, [])

  const selectedMerchant = Array.isArray(merchants)
    ? merchants.find(m => m.id === selectedId)
    : null

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">

        {/* header */}
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-lg font-medium text-gray-900">
            Playto Pay
          </h1>
          <select
            value={selectedId || ''}
            onChange={e => setSelectedId(e.target.value)}
            className="text-sm border border-gray-200 rounded-lg px-3 py-2 bg-white"
          >
            {merchants.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>

        {/* balance cards */}
        <BalanceCards balance={balance} loading={balanceLoading} />

        {/* bottom grid */}
        <div className="grid grid-cols-5 gap-4">
          <div className="col-span-2">
            {selectedId && (
              <PayoutForm
                merchantId={selectedId}
                onSuccess={handlePayoutSuccess}
              />
            )}
          </div>
          <div className="col-span-3">
            {selectedId && (
              <PayoutHistory
                merchantId={selectedId}
                refreshTrigger={refreshTrigger}
              />
            )}
          </div>
        </div>

      </div>
    </div>
  )
}