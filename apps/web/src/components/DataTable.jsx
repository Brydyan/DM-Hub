import { useEffect, useState } from 'react'

// Tabla genérica responsiva con paginación:
// - Pantallas md+: <table> clásica; pantallas pequeñas: tarjetas.
// - Paginación del lado del cliente (10 por defecto, hasta 5000).
// - `renderActions(row)` es opcional y agrega botones de acción por fila.

const PAGE_SIZES = [10, 100, 500, 1000, 5000]

function CellValue({ value }) {
  if (value === null || value === undefined) {
    return <span className="italic text-slate-400">null</span>
  }
  if (typeof value === 'boolean') {
    return (
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-medium ${value ? 'bg-red-100 text-red-700' : 'bg-emerald-100 text-emerald-700'
          }`}
      >
        {String(value)}
      </span>
    )
  }
  return <>{String(value)}</>
}

export default function DataTable({ title, rows, renderActions }) {
  const [page, setPage] = useState(0)
  const [pageSize, setPageSize] = useState(10)

  // Reinicia a la primera página cuando cambia el conjunto de datos
  useEffect(() => setPage(0), [rows])

  if (!rows?.length) return null
  const columns = Object.keys(rows[0])

  const pageCount = Math.max(1, Math.ceil(rows.length / pageSize))
  const current = Math.min(page, pageCount - 1)
  const slice = rows.slice(current * pageSize, (current + 1) * pageSize)

  const btn =
    'rounded-md px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-30 disabled:hover:bg-transparent'

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>

      {/* Vista de tabla: pantallas md en adelante */}
      <div className="mt-3 hidden overflow-x-auto md:block">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  {col}
                </th>
              ))}
              {renderActions && <th className="px-3 py-2" />}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {slice.map((row, i) => (
              <tr key={i} className="hover:bg-slate-50">
                {columns.map((col) => (
                  <td key={col} className="px-3 py-2 text-slate-700">
                    <CellValue value={row[col]} />
                  </td>
                ))}
                {renderActions && (
                  <td className="px-3 py-2 text-right">{renderActions(row)}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Vista de tarjetas: pantallas pequeñas */}
      <div className="mt-3 space-y-3 md:hidden">
        {slice.map((row, i) => (
          <div
            key={i}
            className="rounded-lg border border-slate-200 bg-slate-50 p-3"
          >
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-sm">
              {columns.map((col) => (
                <div key={col}>
                  <dt className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                    {col}
                  </dt>
                  <dd className="text-slate-700">
                    <CellValue value={row[col]} />
                  </dd>
                </div>
              ))}
            </dl>
            {renderActions && (
              <div className="mt-2 flex justify-end gap-2 border-t border-slate-200 pt-2">
                {renderActions(row)}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Controles de paginación */}
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3 text-xs text-slate-500">
        <span>
          {rows.length.toLocaleString()} registros · página {current + 1} de{' '}
          {pageCount}
        </span>
        <div className="flex items-center gap-1">
          <label className="mr-2 flex items-center gap-1">
            Filas:
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(0)
              }}
              className="rounded border border-slate-300 px-1 py-0.5 text-xs"
            >
              {PAGE_SIZES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </label>
          <button
            className={btn}
            disabled={current === 0}
            onClick={() => setPage(0)}
            aria-label="Primera página"
          >
            «
          </button>
          <button
            className={btn}
            disabled={current === 0}
            onClick={() => setPage(current - 1)}
            aria-label="Página anterior"
          >
            ‹
          </button>
          <button
            className={btn}
            disabled={current >= pageCount - 1}
            onClick={() => setPage(current + 1)}
            aria-label="Página siguiente"
          >
            ›
          </button>
          <button
            className={btn}
            disabled={current >= pageCount - 1}
            onClick={() => setPage(pageCount - 1)}
            aria-label="Última página"
          >
            »
          </button>
        </div>
      </div>
    </div>
  )
}
