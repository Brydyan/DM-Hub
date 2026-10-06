import { useEffect, useState } from 'react'
import { LayoutDashboard } from 'lucide-react'
import { apiGet } from '../../api'
import KpiCards from '../../components/KpiCards'
import RegionChart from '../../components/RegionChart'
import DataTable from '../../components/DataTable'

export const meta = {
  id: 'dashboard',
  title: 'Dashboard',
  unit: 'General',
  icon: LayoutDashboard,
  order: 1,
}

// Vista general del warehouse: KPIs, distribución por región y
// estadísticas descriptivas de las variables numéricas.
export default function Dashboard() {
  const [overview, setOverview] = useState(null)
  const [byRegion, setByRegion] = useState([])
  const [summary, setSummary] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      apiGet('/api/stats/overview'),
      apiGet('/api/stats/by-region'),
      apiGet('/api/stats/summary'),
    ])
      .then(([o, r, s]) => {
        setOverview(o)
        setByRegion(r)
        setSummary(s)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-sm text-red-700 ring-1 ring-red-200">
        No se pudo conectar al API: {error}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {overview && <KpiCards overview={overview} />}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {byRegion.length > 0 && <RegionChart data={byRegion} />}
        {summary.length > 0 && (
          <DataTable title="Estadísticas descriptivas" rows={summary} />
        )}
      </div>
    </div>
  )
}
