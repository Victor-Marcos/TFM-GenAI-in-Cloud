import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function PaginaPendientes({ perfil, onVolver }) {
  const [pendientes, setPendientes] = useState([])

  useEffect(() => {
    cargar()
  }, [])

  function cargar() {
    fetch(`${API_URL}/tickets/pendientes?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setPendientes)
  }

  async function validar(ticketId, totalActual) {
    const nuevoTotal = prompt('Corrige el total si hace falta:', totalActual)
    if (nuevoTotal === null) return

    await fetch(`${API_URL}/tickets/${ticketId}/validar?perfil_id=${perfil.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ total_corregido: parseFloat(nuevoTotal) })
    })
    cargar()
  }

  return (
    <div>
      <button onClick={onVolver}>← Volver al menú</button>
      <h1>Tickets pendientes de revisión</h1>

      {pendientes.length === 0 && <p>No tienes tickets pendientes. Todo en orden.</p>}

      <ul>
        {pendientes.map(t => (
          <li key={t.id}>
            {t.comercio} — {t.total}€ — <em>{t.motivo_revision}</em>
            <button onClick={() => validar(t.id, t.total)}>Validar</button>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default PaginaPendientes