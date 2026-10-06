// Gráfico de barras simple en SVG/divs: sin dependencias de charting,
// para que el código sea legible como material didáctico.
export default function RegionChart({ data }) {
  const max = Math.max(...data.map((d) => d.total), 1)
  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h3 className="text-sm font-semibold text-slate-700">Clientes por región</h3>
      <div className="mt-4 space-y-3">
        {data.map((d) => (
          <div key={d.region}>
            <div className="flex justify-between text-xs text-slate-500">
              <span>{d.region}</span>
              <span>{d.total}</span>
            </div>
            <div className="mt-1 h-3 w-full rounded bg-slate-100">
              <div
                className="h-3 rounded bg-indigo-500"
                style={{ width: `${(d.total / max) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
