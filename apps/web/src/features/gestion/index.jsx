import { useEffect, useState } from 'react'
import { Database, Pencil, Plus, Trash2 } from 'lucide-react'
import { apiGet, apiSend } from '../../api'
import DataTable from '../../components/DataTable'
import Modal from '../../components/Modal'
import InfoTip from '../../components/InfoTip'

export const meta = {
  id: 'gestion',
  title: 'Gestión de datos',
  unit: 'U2-T1 · Extracción',
  icon: Database,
  order: 3,
}

const EMPTY_FORM = {
  customer_id: '',
  age: '',
  annual_income: '',
  credit_score: '',
  loan_amount: '',
  has_defaulted: false,
  region: 'Costa',
}

const REGIONS = ['Costa', 'Sierra', 'Oriente', 'Insular']

// Campos del formulario: [clave, etiqueta, tipo]
const FIELDS = [
  ['customer_id', 'ID cliente', 'text'],
  ['age', 'Edad', 'number'],
  ['annual_income', 'Ingreso anual', 'number'],
  ['credit_score', 'Credit score', 'number'],
  ['loan_amount', 'Monto préstamo', 'number'],
]

// Convierte los strings del formulario a los tipos que espera el API.
const toPayload = (form) => ({
  customer_id: form.customer_id,
  age: form.age === '' ? null : Number(form.age),
  annual_income: form.annual_income === '' ? null : Number(form.annual_income),
  credit_score: form.credit_score === '' ? null : Number(form.credit_score),
  loan_amount: form.loan_amount === '' ? null : Number(form.loan_amount),
  has_defaulted: form.has_defaulted,
  region: form.region,
})

// CRUD completo sobre customer_credit_transactions vía API REST:
// UI → API (validación Pydantic) → PostgreSQL con queries parametrizadas.
export default function GestionDatos() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(EMPTY_FORM)
  const [editingId, setEditingId] = useState(null) // null = crear nuevo
  const [showForm, setShowForm] = useState(false)
  const [error, setError] = useState(null)

  const load = () =>
    apiGet('/api/transactions?limit=5000')
      .then(setRows)
      .catch((e) => setError(e.message))

  useEffect(() => {
    load()
  }, [])

  const startCreate = () => {
    setForm(EMPTY_FORM)
    setEditingId(null)
    setShowForm(true)
  }

  const startEdit = (row) => {
    setForm({
      customer_id: row.customer_id ?? '',
      age: row.age ?? '',
      annual_income: row.annual_income ?? '',
      credit_score: row.credit_score ?? '',
      loan_amount: row.loan_amount ?? '',
      has_defaulted: row.has_defaulted ?? false,
      region: row.region ?? 'Costa',
    })
    setEditingId(row.transaction_id)
    setShowForm(true)
  }

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      if (editingId === null) {
        await apiSend('/api/transactions', 'POST', toPayload(form))
      } else {
        await apiSend(`/api/transactions/${editingId}`, 'PUT', toPayload(form))
      }
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const remove = async (row) => {
    if (!window.confirm(`¿Eliminar ${row.customer_id}?`)) return
    setError(null)
    try {
      await apiSend(`/api/transactions/${row.transaction_id}`, 'DELETE')
      await load()
    } catch (err) {
      setError(err.message)
    }
  }

  const actions = (row) => (
    <>
      <button
        onClick={() => startEdit(row)}
        className="rounded-md px-2 py-1 text-xs font-medium text-indigo-600 hover:bg-indigo-50"
      >
        <Pencil className="mr-1 inline h-3 w-3" />
        Editar
      </button>
      <button
        onClick={() => remove(row)}
        className="rounded-md px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50"
      >
        <Trash2 className="mr-1 inline h-3 w-3" />
        Eliminar
      </button>
    </>
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-500">
          Alta, edición y baja de registros sin entrar a la base de datos.
          <InfoTip text="Los botones Editar/Eliminar de cada fila ejecutan PUT y DELETE al API, que actualiza PostgreSQL con queries parametrizadas." />
        </p>
        <span className="inline-flex items-center gap-1">
          <button
            onClick={startCreate}
            className="flex items-center gap-1 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
          >
            <Plus className="h-4 w-4" /> Nuevo registro
          </button>
          <InfoTip text="Abre el formulario para insertar una transacción: se valida con Pydantic en el API antes del INSERT en PostgreSQL." />
        </span>
      </div>

      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </div>
      )}

      <Modal
        open={showForm}
        title={
          editingId === null ? 'Nueva transacción' : `Editar #${editingId}`
        }
        onClose={() => setShowForm(false)}
      >
        <form onSubmit={submit}>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {FIELDS.map(([key, label, type]) => (
              <label key={key} className="block text-xs font-medium text-slate-600">
                {label}
                <input
                  type={type}
                  step={type === 'number' ? 'any' : undefined}
                  required={key === 'customer_id'}
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
                />
              </label>
            ))}
            <label className="block text-xs font-medium text-slate-600">
              Región
              <select
                value={form.region}
                onChange={(e) => setForm({ ...form, region: e.target.value })}
                className="mt-1 w-full rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:border-indigo-500 focus:outline-none"
              >
                {REGIONS.map((r) => (
                  <option key={r}>{r}</option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-2 self-end pb-2 text-xs font-medium text-slate-600">
              <input
                type="checkbox"
                checked={form.has_defaulted}
                onChange={(e) =>
                  setForm({ ...form, has_defaulted: e.target.checked })
                }
                className="h-4 w-4 rounded border-slate-300"
              />
              Incumplió pagos (default)
            </label>
          </div>
          <div className="mt-4 flex gap-2">
            <span className="inline-flex items-center gap-1">
              <button
                type="submit"
                className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
              >
                {editingId === null ? 'Crear' : 'Guardar cambios'}
              </button>
              <InfoTip
                text={
                  editingId === null
                    ? 'Envía el formulario al API (POST): valida los campos e inserta el registro en PostgreSQL.'
                    : 'Envía el formulario al API (PUT): valida los campos y actualiza el registro existente en PostgreSQL.'
                }
              />
            </span>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-200"
            >
              Cancelar
            </button>
          </div>
        </form>
      </Modal>

      <DataTable
        title="customer_credit_transactions"
        rows={rows}
        renderActions={actions}
      />
    </div>
  )
}
