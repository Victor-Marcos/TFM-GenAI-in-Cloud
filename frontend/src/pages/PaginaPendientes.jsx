import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function PaginaPendientes({ perfil, onVolver }) {
  const [pendientes, setPendientes] = useState([])
  const [ticketEnEdicion, setTicketEnEdicion] = useState(null)
  const [imagenAmpliada, setImagenAmpliada] = useState(false)
  const [rotacion, setRotacion] = useState(0)

  useEffect(() => { cargarLista() }, [])

  function cargarLista() {
    fetch(`${API_URL}/tickets/pendientes?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setPendientes)
  }

  async function abrirEdicion(ticketId) {
    const respuesta = await fetch(`${API_URL}/tickets/${ticketId}?perfil_id=${perfil.id}`)
    const detalle = await respuesta.json()
    setTicketEnEdicion(detalle)
  }

  function actualizarCampoLinea(index, campo, valor) {
    setTicketEnEdicion(prev => {
      const productos = [...prev.productos]
      productos[index] = { ...productos[index], [campo]: valor }
      return { ...prev, productos }
    })
  }

  function sumaLineas() {
    return ticketEnEdicion.productos.reduce((acc, p) => acc + parseFloat(p.subtotal || 0), 0)
  }

  function recalcularTotal() {
    setTicketEnEdicion(prev => ({ ...prev, total: sumaLineas().toFixed(2) }))
  }

  async function guardarValidacion() {
    await fetch(`${API_URL}/tickets/${ticketEnEdicion.id}/completo?perfil_id=${perfil.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fecha: ticketEnEdicion.fecha,
        total: parseFloat(ticketEnEdicion.total),
        comercio_nombre: ticketEnEdicion.comercio,
        lineas: ticketEnEdicion.productos.map(p => ({
          id: p.id,
          descripcion_original: p.descripcion_original,
          cantidad: parseFloat(p.cantidad),
          precio_unitario: parseFloat(p.precio_unitario),
          subtotal: parseFloat(p.subtotal)
        }))
      })
    })
    setTicketEnEdicion(null)
    cargarLista()
  }

  async function validarSinCambios(ticketId) {
    await fetch(`${API_URL}/tickets/${ticketId}/validar?perfil_id=${perfil.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    })
    cargarLista()
  }

  async function eliminarTicket(ticketId) {
  const confirmado = confirm('¿Seguro que quieres eliminar este ticket de forma permanente? No se puede deshacer.')
  if (!confirmado) return

  await fetch(`${API_URL}/tickets/${ticketId}?perfil_id=${perfil.id}`, { method: 'DELETE' })
  cargarLista()
}

  // ---- Vista de edición de un ticket ----
  if (ticketEnEdicion) {
    const diferencia = (parseFloat(ticketEnEdicion.total || 0) - sumaLineas()).toFixed(2)

    return (
      <div className="contenedor-app">
        <button onClick={() => setTicketEnEdicion(null)} style={{ marginBottom: '20px' }}>← Volver a la lista</button>
        <h1>Revisar ticket #{ticketEnEdicion.id}</h1>

        {ticketEnEdicion.motivo_revision && (
         <p style={{ color: 'var(--stamp)', fontSize: '13px' }}>{ticketEnEdicion.motivo_revision}</p>
         )}

        <img
          src={`http://localhost:8000/tickets/${ticketEnEdicion.id}/imagen?perfil_id=${perfil.id}`}
          alt="Ticket original"
          onClick={() => { setRotacion(0); setImagenAmpliada(true) }}
          style={{ maxWidth: '300px', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-card)', marginBottom: '20px', cursor: 'zoom-in' }}
        />

        {imagenAmpliada && (
        <div
          onClick={() => setImagenAmpliada(false)}
          style={{
            position: 'fixed', inset: 0, background: 'rgba(31,36,33,0.85)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            zIndex: 100, gap: '16px'
          }}
        >
          <img
            src={`http://localhost:8000/tickets/${ticketEnEdicion.id}/imagen?perfil_id=${perfil.id}`}
            alt="Ticket ampliado"
            style={{
              maxWidth: '85%', maxHeight: '75vh',
              transform: `rotate(${rotacion}deg)`,
              transition: 'transform 0.2s ease',
              borderRadius: 'var(--radius)'
            }}
          />
          <div onClick={e => e.stopPropagation()} style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => setRotacion(r => r - 90)}>↺ Girar izquierda</button>
            <button onClick={() => setRotacion(r => r + 90)}>↻ Girar derecha</button>
            <button onClick={() => setImagenAmpliada(false)} style={{ background: 'var(--stamp)', color: 'white', border: 'none' }}>
              Cerrar
            </button>
          </div>
        </div>
        )}

        <div className="tarjeta-recibo">
          <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
            <label>Comercio
              <input
                value={ticketEnEdicion.comercio}
                onChange={e => setTicketEnEdicion({ ...ticketEnEdicion, comercio: e.target.value })}
                style={{ display: 'block' }}
              />
            </label>
            <label>Fecha
              <input
                type="date"
                value={ticketEnEdicion.fecha}
                onChange={e => setTicketEnEdicion({ ...ticketEnEdicion, fecha: e.target.value })}
                style={{ display: 'block' }}
              />
            </label>
            <label>Total
              <input
                type="number" step="0.01"
                value={ticketEnEdicion.total}
                onChange={e => setTicketEnEdicion({ ...ticketEnEdicion, total: e.target.value })}
                className="mono" style={{ display: 'block' }}
              />
            </label>
          </div>

          <h3 style={{ fontSize: '15px' }}>Productos</h3>
          <table className="mono" style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Descripción</th>
                <th>Cantidad</th>
                <th>Precio</th>
                <th>Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {ticketEnEdicion.productos.map((p, i) => (
                <tr key={p.id}>
                  <td>
                    <input
                      value={p.descripcion_original}
                      onChange={e => actualizarCampoLinea(i, 'descripcion_original', e.target.value)}
                      style={{ width: '100%' }}
                    />
                  </td>
                  <td>
                    <input
                      type="number" step="0.01" value={p.cantidad}
                      onChange={e => actualizarCampoLinea(i, 'cantidad', e.target.value)}
                      style={{ width: '70px' }}
                    />
                  </td>
                  <td>
                    <input
                      type="number" step="0.01" value={p.precio_unitario}
                      onChange={e => actualizarCampoLinea(i, 'precio_unitario', e.target.value)}
                      style={{ width: '80px' }}
                    />
                  </td>
                  <td>
                    <input
                      type="number" step="0.01" value={p.subtotal}
                      onChange={e => actualizarCampoLinea(i, 'subtotal', e.target.value)}
                      style={{ width: '80px' }}
                    />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <p className="mono" style={{ fontSize: '13px', marginTop: '10px', color: diferencia !== '0.00' ? 'var(--stamp)' : 'var(--validated)' }}>
            Suma de líneas: {sumaLineas().toFixed(2)}€ · Diferencia con el total: {diferencia}€
          </p>
          <button onClick={recalcularTotal} style={{ fontSize: '12px', marginBottom: '16px' }}>
            Poner el total igual a la suma de líneas
          </button>

          <div>
            <button onClick={guardarValidacion} style={{ background: 'var(--validated)', color: 'white', border: 'none' }}>
              Guardar y validar
            </button>
          </div>
        </div>
      </div>
    )
  }

  // ---- Vista de lista ----
  return (
    <div className="contenedor-app">
      <button onClick={onVolver} style={{ marginBottom: '20px' }}>← Volver al menú</button>
      <h1>Tickets pendientes de revisión</h1>

      {pendientes.length === 0 && <p>No tienes tickets pendientes. Todo en orden.</p>}

      {pendientes.map(t => (
        <div key={t.id} className="tarjeta-recibo" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong>{t.comercio}</strong> — <span className="mono">{t.total}€</span>
            <div style={{ fontSize: '12px', color: 'var(--ink-soft)', maxWidth: '500px' }}>{t.motivo_revision}</div>
            <div className="mono" style={{ fontSize: '11px', color: 'var(--ink-soft)', marginTop: '4px' }}>
            {t.imagen_path?.split('/').pop()}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => validarSinCambios(t.id)} style={{ fontSize: '12px' }}>Validar sin cambios</button>
          <button onClick={() => abrirEdicion(t.id)} style={{ background: 'var(--ink)', color: 'var(--paper)', border: 'none', fontSize: '12px' }}>
            Revisar y corregir
          </button>
          <button onClick={() => eliminarTicket(t.id)} style={{ background: 'var(--stamp)', color: 'white', border: 'none', fontSize: '12px' }}>
            Eliminar
          </button>
          </div>
        </div>
      ))}
    </div>
  )
}

export default PaginaPendientes