import { Info } from 'lucide-react'
import { useState } from 'react'

// Icono informativo reutilizable: explica qué hace el botón asociado.
// Se muestra al pasar el cursor (desktop) o al tocar el icono (móvil).
export default function InfoTip({ text }) {
  const [open, setOpen] = useState(false)
  return (
    <span className="group relative inline-flex items-center">
      <button
        type="button"
        aria-label="¿Qué hace este botón?"
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setOpen(false)}
        className="rounded-full p-0.5 text-slate-400 transition hover:text-indigo-500 focus:text-indigo-600 focus:outline-none"
      >
        <Info size={14} />
      </button>
      <span
        role="tooltip"
        className={`pointer-events-none absolute bottom-full left-1/2 z-30 mb-2 w-64 -translate-x-1/2 rounded-lg bg-slate-800 p-3 text-left text-xs font-normal leading-relaxed text-slate-100 shadow-lg ring-1 ring-slate-700 transition-opacity ${
          open ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'
        }`}
      >
        {text}
      </span>
    </span>
  )
}
