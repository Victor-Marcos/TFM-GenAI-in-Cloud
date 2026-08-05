import { useState } from 'react'
import { subirTicket } from '../services/api.js'

function PaginaCargaDatos({ perfil, onVolver }) {
  const [ficheros, setFicheros] = useState([])
  const [resultados, setResultados] = useState([])
  const [procesando, setProcesando] = useState(false)

  function manejarSeleccion(evento) {
    setFicheros(Array.from(evento.target.files))
  }

  async function subirTodos() {
    setProcesando(true)
    setResultados([])

    for (const fichero of ficheros) {
      try {
        const datos = await subirTicket(fichero, perfil.id)
        setResultados(previos => [...previos, { nombre: fichero.name, ...datos }])
      } catch (error) {
        setResultados(previos => [...previos, { nombre: fichero.name, estado: 'error_red' }])
      }
    }

    setProcesando(false)
    setFicheros([])
  }

  return (
    <div>
      <button onClick={onVolver}>← Volver al menú</button>
      <h1>Subir tickets</h1>

      <input type="file" accept="image/*" multiple onChange={manejarSeleccion} />
      {ficheros.length > 0 && (
        <p>{ficheros.length} imagen(es) seleccionada(s)</p>
      )}

      <button onClick={subirTodos} disabled={ficheros.length === 0 || procesando}>
        {procesando ? 'Procesando...' : 'Subir y procesar'}
      </button>

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