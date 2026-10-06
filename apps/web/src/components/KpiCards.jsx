export default function KpiCards({ overview }) {
  const cards = [
    { label: 'Clientes', value: overview.total_customers },
    { label: 'Regiones', value: overview.total_regions },
    { label: 'Tasa de default', value: `${overview.default_rate_pct}%` },
  ]
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <p className="text-sm font-medium text-slate-500">{c.label}</p>
          <p className="mt-1 text-3xl font-semibold text-slate-900">{c.value}</p>
        </div>
      ))}
    </div>
  )
}
