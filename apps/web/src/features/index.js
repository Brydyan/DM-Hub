// ═══════════════════════════════════════════════════════════════════
// REGISTRO DE FUNCIONALIDADES — contrato "feature folder"
// ═══════════════════════════════════════════════════════════════════
//
// Para agregar una funcionalidad nueva al menú lateral basta con crear
// una carpeta `features/<mi-feature>/index.jsx` que exporte:
//
//   export const meta = {
//     id: 'mi-feature',        // identificador único
//     title: 'Mi Feature',     // texto en el menú
//     unit: 'U3',              // unidad del silabo (agrupa el menú)
//     icon: MiIcono,           // componente de icono (lucide-react)
//     order: 10,               // posición dentro del menú
//     ready: true,             // false → aparece deshabilitada
//   }
//   export default function MiFeature() { ... }
//
// `import.meta.glob` descubre los módulos en build-time; no hay que
// modificar App.jsx ni el Sidebar para que la opción aparezca.
// ═══════════════════════════════════════════════════════════════════

const modules = import.meta.glob('./*/index.jsx', { eager: true })

export const features = Object.entries(modules)
  .map(([path, mod]) => ({
    path,
    Component: mod.default,
    ...(mod.meta ?? {}),
  }))
  .filter((f) => f.id && f.Component)
  .sort((a, b) => (a.order ?? 99) - (b.order ?? 99))
