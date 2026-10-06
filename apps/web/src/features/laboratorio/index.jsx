import { useState } from 'react'
import { FlaskConical } from 'lucide-react'
import { apiGet } from '../../api'
import DataTable from '../../components/DataTable'
import InfoTip from '../../components/InfoTip'

export const meta = {
  id: 'laboratorio',
  title: 'Laboratorio U2-T1',
  unit: 'U2-T1 · Extracción',
  icon: FlaskConical,
  order: 2,
}

// Ejercicios de la hoja de trabajo U2-T1 ejecutados contra el API.
const EXERCISES = [
  {
    id: 1,
    name: 'Conteo por región',
    path: '/api/stats/by-region',
    description:
      'Ejecuta GROUP BY region en PostgreSQL: cuenta cuántas transacciones hay por cada región y las ordena de mayor a menor.',
  },
  {
    id: 2,
    name: 'Perfil de riesgo (score < 650)',
    path: '/api/stats/risk-profile?threshold=650',
    description:
      'Filtra con WHERE credit_score < 650 para identificar clientes de mayor riesgo crediticio, ordenados de menor a mayor score.',
  },
  {
    id: 3,
    name: 'Costa por ingreso desc.',
    path: '/api/transactions?region=Costa&order_by_income=true',
    description:
      'Combina WHERE region = Costa con ORDER BY annual_income DESC: las transacciones de la Costa ordenadas por ingreso.',
  },
  {
    id: 4,
    name: 'Tabla completa',
    path: '/api/transactions?limit=5000',
    description:
      'SELECT * sobre toda la tabla: equivale a unir los lotes que produciría la extracción por chunks del conector Python.',
  },
]

export default function Laboratorio() {
  const [result, setResult] = useState(null)
  const [active, setActive] = useState(null)
  const [error, setError] = useState(null)

  const run = async (exercise) => {
    setActive(exercise.id)
    setError(null)
    try {
      setResult({ title: exercise.name, rows: await apiGet(exercise.path) })
    } catch (e) {
      setResult(null)
      setError(e.message)
    }
  }

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <h3 className="text-sm font-semibold text-slate-700">
        Ejercicios de extracción — hoja de trabajo U2-T1
      </h3>
      <div className="mt-3 flex flex-wrap gap-2">
        {EXERCISES.map((ex) => (
          <span key={ex.id} className="inline-flex items-center gap-1">
            <button
              onClick={() => run(ex)}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition ${active === ex.id
                ? 'bg-indigo-600 text-white'
                : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
            >
              {ex.id}. {ex.name}
            </button>
            <InfoTip text={ex.description} />
          </span>
        ))}
      </div>
      {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      <div className="mt-4">
        {result && <DataTable title={result.title} rows={result.rows} />}
      </div>
    </div>
  )
}
