import { useCallback, useEffect, useState } from 'react'
import { BrushCleaning, Play } from 'lucide-react'
import { apiGet, apiSend } from '../../api'
import DataTable from '../../components/DataTable'
import InfoTip from '../../components/InfoTip'

export const meta = {
  id: 'limpieza',
  title: 'Limpieza y calidad',
  unit: 'U2-T3 · Limpieza',
  icon: BrushCleaning,
  order: 5,
}

const NUMERIC = ['age', 'annual_income', 'credit_score', 'loan_amount']

const RETOS = [
  'Compara la media vs la mediana imputando annual_income: ¿por qué la mediana es más robusta ante outliers?',
  'Ejecuta la detección IQR y Z-score sobre loan_amount: ¿cuántos outliers detecta cada método?',
  'Tras correr el pipeline, audita la tabla limpia: ¿qué defectos persisten y por qué?',
  'El capping preserva filas pero altera el dato original: ¿en qué escenario preferirías drop?',
]

const label = { mean: 'Media', median: 'Mediana', mode: 'Moda', knn: 'KNN (avanzada)' }

function StatCompare({ report }) {
  if (!report) return null
  const keys = ['nulls', 'mean', 'median', 'std', 'min', 'max', 'unique']
  const rows = keys.filter((k) => report.before[k] !== undefined)
  return (
    <table className="mt-3 w-full text-left text-xs">
      <thead>
        <tr className="text-slate-500">
          <th className="py-1"></th>
          {rows.map((k) => (
            <th key={k} className="py-1 font-medium">{k}</th>
          ))}
        </tr>
      </thead>
      <tbody className="text-slate-700">
        <tr>
          <td className="py-1 font-medium text-slate-500">Antes</td>
          {rows.map((k) => (
            <td key={k} className="py-1">{report.before[k] ?? '—'}</td>
          ))}
        </tr>
        <tr className="font-semibold text-emerald-700">
          <td className="py-1 font-medium text-slate-500">Después</td>
          {rows.map((k) => (
            <td key={k} className="py-1">{report.after[k] ?? '—'}</td>
          ))}
        </tr>
      </tbody>
    </table>
  )
}

// Laboratorio U2-T3: la "tríada patológica" (faltantes, inconsistencias,
// outliers) sobre la tabla cruda, y un pipeline que materializa
// customer_credit_clean para la práctica demostrativa.
export default function Limpieza() {
  const [audit, setAudit] = useState(null)
  const [impCol, setImpCol] = useState('annual_income')
  const [impStrategy, setImpStrategy] = useState('median')
  const [impReport, setImpReport] = useState(null)
  const [outCol, setOutCol] = useState('annual_income')
  const [outMethod, setOutMethod] = useState('iqr')
  const [outAction, setOutAction] = useState('cap')
  const [outReport, setOutReport] = useState(null)
  const [norm, setNorm] = useState(null)
  const [runResult, setRunResult] = useState(null)
  const [cleanRows, setCleanRows] = useState([])
  const [error, setError] = useState(null)
  const [running, setRunning] = useState(false)

  const refreshAudit = useCallback(
    () => apiGet('/api/cleaning/audit').then(setAudit).catch((e) => setError(e.message)),
    []
  )

  useEffect(() => {
    refreshAudit()
    apiGet('/api/cleaning/preview/normalization').then(setNorm).catch(() => { })
  }, [refreshAudit])

  const previewImpute = () =>
    apiGet(`/api/cleaning/preview/imputation?column=${impCol}&strategy=${impStrategy}`)
      .then(setImpReport)
      .catch((e) => setError(e.message))

  const previewOutliers = () =>
    apiGet(
      `/api/cleaning/preview/outliers?column=${outCol}&method=${outMethod}&action=${outAction}`
    )
      .then(setOutReport)
      .catch((e) => setError(e.message))

  const runPipeline = async () => {
    setRunning(true)
    setError(null)
    try {
      const result = await apiSend('/api/cleaning/run', 'POST')
      setRunResult(result)
      const rows = await apiGet('/api/cleaning/rows?target=clean&limit=5000')
      setCleanRows(rows)
    } catch (e) {
      setError(e.message)
    } finally {
      setRunning(false)
    }
  }

  const fieldCls =
    'mt-1 block rounded-lg border border-slate-300 px-2 py-1.5 text-sm'
  const labelCls = 'text-xs font-medium text-slate-600'
  const btnCls =
    'rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700'

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {/* Auditoría de calidad sobre la tabla cruda */}
      {audit && (
        <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <h3 className="text-sm font-semibold text-slate-700">
            Auditoría de calidad — tabla cruda ({audit.rows} registros)
          </h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[
              ['Duplicados', audit.duplicates],
              ['Nulos totales', audit.columns.reduce((a, c) => a + c.nulls, 0)],
              [
                'Variantes de región',
                audit.columns.find((c) => c.column === 'region')?.unique ?? '—',
              ],
              [
                'Fuera de rango',
                audit.columns.reduce((a, c) => a + (c.out_of_range ?? 0), 0),
              ],
            ].map(([k, v]) => (
              <div
                key={k}
                className="rounded-lg bg-slate-50 p-3 text-center ring-1 ring-slate-100"
              >
                <p className="text-2xl font-bold text-slate-800">{v}</p>
                <p className="text-xs text-slate-500">{k}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="text-slate-500">
                  <th className="py-1">Columna</th>
                  <th className="py-1">Nulos</th>
                  <th className="py-1">% nulos</th>
                  <th className="py-1">Outliers IQR</th>
                  <th className="py-1">Fuera de rango</th>
                </tr>
              </thead>
              <tbody className="text-slate-700">
                {audit.columns.map((c) => (
                  <tr key={c.column} className="border-t border-slate-100">
                    <td className="py-1 font-mono">{c.column}</td>
                    <td className="py-1">{c.nulls}</td>
                    <td className="py-1">{c.null_pct}%</td>
                    <td className="py-1">{c.outliers_iqr ?? '—'}</td>
                    <td className="py-1">{c.out_of_range ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Estación 1: faltantes — imputación */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 className="text-sm font-semibold text-slate-700">
          1 · Valores faltantes — imputación
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Reemplazo sin eliminar la fila. La media y la mediana reducen la
          varianza; KNN imputa según los registros más similares.
        </p>
        <div className="mt-3 flex flex-wrap items-end gap-4">
          <label className={labelCls}>
            Columna
            <select
              value={impCol}
              onChange={(e) => setImpCol(e.target.value)}
              className={fieldCls}
            >
              {[...NUMERIC, 'region'].map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className={labelCls}>
            Estrategia
            <select
              value={impStrategy}
              onChange={(e) => setImpStrategy(e.target.value)}
              className={fieldCls}
            >
              {Object.entries(label).map(([v, l]) => (
                <option key={v} value={v}>
                  {l}
                </option>
              ))}
            </select>
          </label>
          <span className="inline-flex items-center gap-1">
            <button onClick={previewImpute} className={btnCls}>
              Previsualizar
            </button>
            <InfoTip text="Imputa los valores faltantes de la columna con la estrategia elegida y muestra las estadísticas antes/después. Se calcula en memoria: no modifica la base de datos." />
          </span>
          {impReport && (
            <span className="text-xs text-slate-500">
              {impReport.imputed} valor(es) imputado(s) — desvío estándar antes:{' '}
              {impReport.before.std ?? '—'} → después:{' '}
              {impReport.after.std ?? '—'}
            </span>
          )}
        </div>
        <StatCompare report={impReport} />
      </div>

      {/* Estación 2: inconsistencias */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 className="text-sm font-semibold text-slate-700">
          2 · Inconsistencias — normalización
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Integración de fuentes heterogéneas: espacios y mayúsculas fragmentan
          las categorías. Se tipifica con strip + título y los rangos inválidos
          pasan a NaN para ser imputados.
        </p>
        {norm && (
          <div className="mt-3 grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-xs font-medium text-slate-600">
                Variantes de region tras normalizar (
                {norm.region.normalized} valores corregidos):
              </p>
              <ul className="mt-2 space-y-1 text-xs text-slate-700">
                {Object.entries(norm.region.variants_after).map(([k, v]) => (
                  <li key={k} className="flex justify-between">
                    <span className="font-mono">{k}</span>
                    <span>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-xs font-medium text-slate-600">
                Valores fuera de rango de negocio (→ NaN):
              </p>
              <ul className="mt-2 space-y-1 text-xs text-slate-700">
                {Object.entries(norm.range_violations).map(([k, v]) => (
                  <li key={k} className="flex justify-between">
                    <span className="font-mono">{k}</span>
                    <span>{v}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Estación 3: outliers */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 className="text-sm font-semibold text-slate-700">
          3 · Outliers — detección y tratamiento
        </h3>
        <p className="mt-1 text-xs text-slate-500">
          Detección por IQR (1.5×rango intercuartílico) o Z-score (|z| &gt; 3).
          Tratamiento: eliminar filas, acotar al límite (capping) o suavizar
          con log — la decisión depende de las reglas de negocio.
        </p>
        <div className="mt-3 flex flex-wrap items-end gap-4">
          <label className={labelCls}>
            Columna
            <select
              value={outCol}
              onChange={(e) => setOutCol(e.target.value)}
              className={fieldCls}
            >
              {NUMERIC.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </label>
          <label className={labelCls}>
            Detección
            <select
              value={outMethod}
              onChange={(e) => setOutMethod(e.target.value)}
              className={fieldCls}
            >
              <option value="iqr">IQR (1.5×)</option>
              <option value="zscore">Z-score (|z|&gt;3)</option>
            </select>
          </label>
          <label className={labelCls}>
            Acción
            <select
              value={outAction}
              onChange={(e) => setOutAction(e.target.value)}
              className={fieldCls}
            >
              <option value="cap">Acotamiento (cap)</option>
              <option value="drop">Eliminar filas</option>
              <option value="log">Transformación log</option>
            </select>
          </label>
          <span className="inline-flex items-center gap-1">
            <button onClick={previewOutliers} className={btnCls}>
              Previsualizar
            </button>
            <InfoTip text="Detecta los outliers de la columna con el método elegido y previsualiza el efecto de la acción (drop, cap o log). Se calcula en memoria: no modifica la base de datos." />
          </span>
          {outReport && (
            <span className="text-xs text-slate-500">
              {outReport.detected} outlier(s) detectado(s) —{' '}
              {outReport.rows_after} filas resultantes
            </span>
          )}
        </div>
        <StatCompare report={outReport} />
      </div>

      {/* Pipeline: raw -> clean */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-sm font-semibold text-slate-700">
            Pipeline de calidad — ejecutar limpieza completa
          </h3>
          <span className="inline-flex items-center gap-1">
            <button
              onClick={runPipeline}
              disabled={running}
              className="flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
            >
              <Play size={14} />
              {running ? 'Ejecutando…' : 'Ejecutar pipeline'}
            </button>
            <InfoTip text="Sí escribe en la base de datos: ejecuta toda la cadena de limpieza sobre la tabla cruda y guarda el resultado en customer_credit_clean (la tabla cruda permanece intacta)." />
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-500">
          Aplica: normalización → deduplicación → imputación (mediana/moda) →
          capping IQR. Escribe el resultado en{' '}
          <code className="rounded bg-slate-100 px-1">customer_credit_clean</code>{' '}
          sin tocar la tabla cruda (patrón ETL).
        </p>
        {runResult && (
          <div className="mt-3 space-y-2 text-xs text-slate-600">
            <p className="font-medium text-emerald-700">
              {runResult.rows_in} filas crudas → {runResult.rows_out} filas
              limpias en '{runResult.clean_table}'
            </p>
            <ol className="list-decimal space-y-1 pl-5">
              {runResult.steps.map((s, i) => (
                <li key={i}>
                  <span className="font-medium">{s.step}</span>
                  {s.detail.imputed !== undefined &&
                    ` — ${s.detail.imputed} imputado(s)`}
                  {s.detail.detected !== undefined &&
                    ` — ${s.detail.detected} outlier(s)`}
                  {s.detail.removed !== undefined &&
                    ` — ${s.detail.removed} eliminado(s)`}
                  {s.detail.region &&
                    ` — ${s.detail.region.normalized} región(es) corregida(s)`}
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>

      {/* Dataset limpio materializado */}
      {cleanRows.length > 0 && (
        <DataTable
          title={`Dataset limpio (${cleanRows.length} registros)`}
          rows={cleanRows}
        />
      )}

      {/* Retos */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <h3 className="text-sm font-semibold text-slate-700">
          Retos de la sesión práctica
        </h3>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-slate-600">
          {RETOS.map((r, i) => (
            <li key={i}>{r}</li>
          ))}
        </ol>
      </div>
    </div>
  )
}
