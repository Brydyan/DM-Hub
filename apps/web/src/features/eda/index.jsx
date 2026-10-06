import { useEffect, useState } from 'react'
import { BarChart3 } from 'lucide-react'
import { apiGet } from '../../api'
import DataTable from '../../components/DataTable'
import InfoTip from '../../components/InfoTip'

export const meta = {
  id: 'eda',
  title: 'EDA — Servidor',
  unit: 'U2-T2 · EDA',
  icon: BarChart3,
  order: 4,
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const RETOS = [
  'Cambia los bins del histograma (5 vs 200): ¿cómo altera la percepción del mismo dataset?',
  'Sustituye el panel de densidad por el scatter de usuarios vs. tiempo: ¿hay correlación?',
  'Aísla con el filtro los registros con tiempo_respuesta > 250 ms.',
  'Activa el hue por servidor y compara los dos boxplot generados.',
]

// EDA del notebook U2_T2: figura matplotlib 2x2 servida como PNG por el API,
// con controles que convierten los retos de la sesión en interactivos.
export default function Eda() {
  const [bins, setBins] = useState(30)
  const [panelB, setPanelB] = useState('density')
  const [hueServer, setHueServer] = useState(false)
  const [summary, setSummary] = useState([])
  const [threshold, setThreshold] = useState(250)
  const [outliers, setOutliers] = useState([])
  const [error, setError] = useState(null)

  const figUrl = `${API_URL}/api/eda/figure?bins=${bins}&panel_b=${panelB}&hue_server=${hueServer}`

  useEffect(() => {
    apiGet('/api/eda/summary').then(setSummary).catch((e) => setError(e.message))
    apiGet('/api/eda/outliers?threshold=250')
      .then(setOutliers)
      .catch(() => { })
  }, [])

  const runOutliers = () =>
    apiGet(`/api/eda/outliers?threshold=${threshold}`)
      .then(setOutliers)
      .catch((e) => setError(e.message))

  return (
    <div className="space-y-6">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      {/* Controles = retos interactivos */}
      <div className="flex flex-wrap items-end gap-4 rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <label className="text-xs font-medium text-slate-600">
          Bins (Reto 1)
          <select
            value={bins}
            onChange={(e) => setBins(Number(e.target.value))}
            className="mt-1 block rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
          >
            {[5, 10, 30, 50, 100, 200].map((b) => (
              <option key={b} value={b}>
                {b}
              </option>
            ))}
          </select>
        </label>
        <label className="text-xs font-medium text-slate-600">
          Panel B (Reto 2)
          <select
            value={panelB}
            onChange={(e) => setPanelB(e.target.value)}
            className="mt-1 block rounded-lg border border-slate-300 px-2 py-1.5 text-sm"
          >
            <option value="density">Densidad (KDE)</option>
            <option value="scatter">Scatter usuarios vs tiempo</option>
          </select>
        </label>
        <label className="flex items-center gap-2 pb-2 text-xs font-medium text-slate-600">
          <input
            type="checkbox"
            checked={hueServer}
            onChange={(e) => setHueServer(e.target.checked)}
            className="h-4 w-4 rounded border-slate-300"
          />
          Boxplot por servidor (Reto 4)
        </label>
      </div>

      {/* Figura generada en el servidor con matplotlib/seaborn */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <img
          key={figUrl}
          src={figUrl}
          alt="Figura EDA 2x2 generada por matplotlib"
          className="w-full rounded-lg"
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {summary.length > 0 && (
          <DataTable title="Estadísticas del dataset (1000 filas)" rows={summary} />
        )}
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

      {/* Reto 3: aislamiento de outliers */}
      <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
        <div className="flex flex-wrap items-center gap-3">
          <h3 className="text-sm font-semibold text-slate-700">
            Aislamiento de outliers (Reto 3)
          </h3>
          <label className="text-xs font-medium text-slate-600">
            Umbral (ms)
            <input
              type="number"
              value={threshold}
              onChange={(e) => setThreshold(Number(e.target.value))}
              className="ml-2 w-24 rounded-lg border border-slate-300 px-2 py-1 text-sm"
            />
          </label>
          <span className="inline-flex items-center gap-1">
            <button
              onClick={runOutliers}
              className="rounded-lg bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Filtrar
            </button>
            <InfoTip text="Devuelve los registros cuyo tiempo_respuesta supera el umbral indicado — el Reto 3 del notebook: aislar los outliers para inspeccionarlos." />
          </span>
          <span className="text-xs text-slate-500">
            {outliers.length} registro(s) por encima del umbral
          </span>
        </div>
        <div className="mt-3">
          {outliers.length > 0 && (
            <DataTable title="Registros aislados" rows={outliers} />
          )}
        </div>
      </div>
    </div>
  )
}
