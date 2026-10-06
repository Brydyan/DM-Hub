import { Database, X } from 'lucide-react'

// Menú lateral responsivo con tres estados:
// - Móvil (<md): oculto por defecto; se abre como panel superpuesto (drawer).
// - Escritorio expandido: icono + texto + secciones por unidad.
// - Escritorio colapsado (`collapsed`): solo iconos.
// Las funcionalidades llegan ya registradas desde src/features.
export default function Sidebar({
  features,
  activeId,
  onSelect,
  health,
  collapsed,
  mobileOpen,
  onClose,
}) {
  const units = [...new Set(features.map((f) => f.unit))]
  const apiOk = health?.status === 'ok'

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white transition-all duration-200
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
        md:static md:translate-x-0 ${collapsed ? 'md:w-16' : 'md:w-64'}`}
    >
      <div
        className={`flex items-center justify-between border-b border-slate-200 px-5 py-4 ${collapsed ? 'md:justify-center md:px-2' : ''
          }`}
      >
        {collapsed && (
          <Database className="hidden h-5 w-5 text-indigo-600 md:block" />
        )}
        <div className={collapsed ? 'md:hidden' : ''}>
          <h1 className="text-base font-bold text-slate-900">Data Mining Hub</h1>
          <p className="text-xs text-slate-500">Minería de Datos · UPSE</p>
        </div>
        <button
          onClick={onClose}
          aria-label="Cerrar menú"
          className="rounded-lg p-1 text-slate-500 hover:bg-slate-100 md:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {units.map((unit) => (
          <div key={unit}>
            <p
              className={`px-2 pb-1 text-xs font-semibold uppercase tracking-wide text-slate-400 ${collapsed ? 'md:hidden' : ''
                }`}
            >
              {unit}
            </p>
            {features
              .filter((f) => f.unit === unit)
              .map((f) => {
                const Icon = f.icon
                const disabled = f.ready === false
                return (
                  <button
                    key={f.id}
                    title={f.title}
                    onClick={() => !disabled && onSelect(f.id)}
                    disabled={disabled}
                    className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm font-medium transition ${collapsed ? 'md:justify-center md:px-0' : ''
                      } ${activeId === f.id
                        ? 'bg-indigo-50 text-indigo-700'
                        : disabled
                          ? 'cursor-not-allowed text-slate-300'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span className={`flex-1 ${collapsed ? 'md:hidden' : ''}`}>
                      {f.title}
                    </span>
                    {disabled && (
                      <span
                        className={`rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-400 ${collapsed ? 'md:hidden' : ''
                          }`}
                      >
                        próximo
                      </span>
                    )}
                  </button>
                )
              })}
          </div>
        ))}
      </nav>

      <div
        className={`border-t border-slate-200 px-5 py-3 ${collapsed ? 'md:px-0 md:text-center' : ''
          }`}
      >
        <span
          className={`inline-flex items-center gap-2 text-xs font-medium ${apiOk ? 'text-emerald-600' : 'text-red-600'
            }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${apiOk ? 'bg-emerald-500' : 'bg-red-500'
              }`}
          />
          <span className={collapsed ? 'md:hidden' : ''}>
            API {apiOk ? 'conectada' : 'sin conexión'}
          </span>
        </span>
      </div>
    </aside>
  )
}
