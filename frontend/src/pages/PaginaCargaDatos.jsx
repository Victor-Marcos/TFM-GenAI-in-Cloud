import { subirTicket } from '../services/api.js'

function PaginaCargaDatos({ perfil, onVolver, ficheros, setFicheros, resultados, setResultados, procesando, setProcesando, cancelarRef, progreso, setProgreso }) {
  function manejarSeleccion(evento) {
    setFicheros(Array.from(evento.target.files))
  }

  async function subirTodos() {
    cancelarRef.current = false
    setProcesando(true)
    setResultados([])
    setProgreso({ actual: 0, total: ficheros.length })

    for (let i = 0; i < ficheros.length; i++) {
      if (cancelarRef.current) break
      const fichero = ficheros[i]

      try {
        const datos = await subirTicket(fichero, perfil.id)
        setResultados(previos => [...previos, { nombre: fichero.name, ...datos }])
      } catch (error) {
        setResultados(previos => [...previos, { nombre: fichero.name, estado: 'error_red' }])
      }

      setProgreso({ actual: i + 1, total: ficheros.length })
      await new Promise(resolve => setTimeout(resolve, 4000))
    }

    setProcesando(false)
    setFicheros([])
  }

  function detener() {
    cancelarRef.current = true
  }

  const porcentaje = progreso.total > 0 ? Math.round((progreso.actual / progreso.total) * 100) : 0

  return (
    <div className="contenedor-app">
      <button onClick={onVolver} style={{ marginBottom: '20px' }}>← Volver al menú</button>
      <h1>Subir tickets</h1>

      <input type="file" accept="image/*" multiple onChange={manejarSeleccion} disabled={procesando} />
      {ficheros.length > 0 && <p>{ficheros.length} imagen(es) seleccionada(s)</p>}

      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        <button onClick={subirTodos} disabled={ficheros.length === 0 || procesando}>
          {procesando ? 'Procesando...' : 'Subir y procesar'}
        </button>
        {procesando && (
          <button onClick={detener} style={{ background: 'var(--stamp)', color: 'white', border: 'none' }}>
            Detener
          </button>
        )}
      </div>

      {(procesando || progreso.total > 0) && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ background: 'var(--line)', borderRadius: '999px', height: '10px', overflow: 'hidden' }}>
            <div
              style={{
                width: `${porcentaje}%`,
                background: porcentaje === 100 ? 'var(--validated)' : 'var(--stamp)',
                height: '100%',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
          <p className="mono" style={{ fontSize: '12px', color: 'var(--ink-soft)', marginTop: '6px' }}>
            {progreso.actual} / {progreso.total} ({porcentaje}%)
          </p>
        </div>
      )}

      <ul>
        {resultados.map((r, i) => (
          <li key={i}>
            {r.nombre}: {r.estado}
            {r.motivo_revision && ` (${r.motivo_revision})`}
          </li>
        ))}
      </ul>
    </div>
  )
}

export default PaginaCargaDatos