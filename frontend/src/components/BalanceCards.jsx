export default function BalanceCards({ balance, loading }) {
  const fmt = (paise) => `₹${(paise / 100).toLocaleString('en-IN')}`

  if (loading) return (
    <div className="grid grid-cols-3 gap-3 mb-6">
      {[1,2,3].map(i => (
        <div key={i} className="bg-gray-100 rounded-lg p-4 animate-pulse h-20"/>
      ))}
    </div>
  )

  return (
    <div className="grid grid-cols-3 gap-3 mb-6">
      <div className="bg-gray-50 rounded-lg p-4">
        <p className="text-xs text-gray-500 mb-1">Total balance</p>
        <p className="text-2xl font-medium text-gray-900">
          {fmt(balance?.total_balance_paise || 0)}
        </p>
      </div>
      <div className="bg-amber-50 rounded-lg p-4">
        <p className="text-xs text-amber-600 mb-1">Held</p>
        <p className="text-2xl font-medium text-amber-700">
          {fmt(balance?.held_balance_paise || 0)}
        </p>
      </div>
      <div className="bg-green-50 rounded-lg p-4">
        <p className="text-xs text-green-600 mb-1">Available</p>
        <p className="text-2xl font-medium text-green-700">
          {fmt(balance?.available_balance_paise || 0)}
        </p>
      </div>
    </div>
  )
}