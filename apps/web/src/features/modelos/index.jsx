import { BrainCircuit } from 'lucide-react'

export const meta = {
  id: 'modelos',
  title: 'Modelos predictivos',
  unit: 'U3 · Modelado',
  order: 6,
  icon: BrainCircuit,
  ready: false, // se habilita cuando existan endpoints /api/predict, /api/cluster
}

// Placeholder de la Unidad 3 del silabo: clasificación (default de
// crédito), regresión y clustering K-Means.
export default function Modelos() {
  return (
    <div className="rounded-xl border-2 border-dashed border-slate-300 bg-slate-50 p-10 text-center">
      <p className="text-sm font-medium text-slate-500">
        Disponible en la Unidad 3 — Modelado Predictivo
      </p>
      <p className="mt-1 text-xs text-slate-400">
        Aquí se consumirán los endpoints de clasificación, regresión y
        clustering expuestos por el API.
      </p>
    </div>
  )
}
