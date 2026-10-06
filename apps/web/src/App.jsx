import { useEffect, useState } from 'react'
import { Menu } from 'lucide-react'
import { apiGet } from './api'
import { features } from './features'
import Sidebar from './components/Sidebar'

export default function App() {
  const [activeId, setActiveId] = useState(features[0]?.id)
  const [health, setHealth] = useState(null)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)

  useEffect(() => {
    apiGet('/api/health')
      .then(setHealth)
      .catch(() => setHealth({ status: 'error' }))
  }, [])

  const active =
    features.find((f) => f.id === activeId && f.ready !== false) ?? features[0]
  const ActiveComponent = active.Component

  // El botón hamburguesa actúa según el tamaño de pantalla:
  // escritorio (md+) → colapsa/expande a "solo iconos"; móvil → abre/cierra el drawer.
  const toggleSidebar = () => {
    if (window.matchMedia('(min-width: 768px)').matches) {
      setCollapsed((c) => !c)
    } else {
      setMobileOpen((o) => !o)
    }
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      {/* Fondo oscuro cuando el drawer está abierto en móvil */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-30 bg-slate-900/50 md:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <Sidebar
        features={features}
        activeId={active.id}
        onSelect={(id) => {
          setActiveId(id)
          setMobileOpen(false)
        }}
        health={health}
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onClose={() => setMobileOpen(false)}
      />

      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <header className="mb-6 flex items-center gap-3">
          <button
            onClick={toggleSidebar}
            aria-label="Alternar menú"
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-200"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div>
            <h2 className="text-xl font-bold text-slate-900">{active.title}</h2>
            <p className="text-xs text-slate-400">{active.unit}</p>
          </div>
        </header>
        <ActiveComponent />
      </main>
    </div>
  )
}
