import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function PaginaPerfiles({ onSeleccionarPerfil }) {
  const [perfiles, setPerfiles] = useState([])
  const [nombreNuevo, setNombreNuevo] = useState('')
  const [descripcionNueva, setDescripcionNueva] = useState('')
  const [panelAbierto, setPanelAbierto] = useState(false)

  useEffect(() => { cargar() }, [])

  function cargar() {
    fetch(`${API_URL}/perfiles`).then(r => r.json()).then(setPerfiles)
  }

  async function crearPerfil() {
    if (!nombreNuevo.trim()) return
    await fetch(`${API_URL}/perfiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre: nombreNuevo, descripcion: descripcionNueva })
    })
    setNombreNuevo('')
    setDescripcionNueva('')
    cargar()
  }

  async function eliminarPerfil(perfil) {
    const confirmacion = prompt(
      `Esto borrará el perfil "${perfil.nombre}" y TODOS sus tickets de forma permanente.\nEscribe "eliminar perfil" para confirmar:`
    )
    if (confirmacion !== 'eliminar perfil') {
      if (confirmacion !== null) alert('Texto incorrecto. No se ha eliminado nada.')
      return
    }
    await fetch(`${API_URL}/perfiles/${perfil.id}`, { method: 'DELETE' })
    cargar()
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ padding: '28px 32px' }}>
        <span className="mono" style={{ fontSize: '13px', letterSpacing: '0.12em', color: 'var(--ink-soft)' }}>
          TFM Víctor Marcos · GENAI IN CLOUD
        </span>
      </header>

      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '36px' }}>
        <h1 style={{ fontSize: '30px' }}>Selecciona tu perfil</h1>

        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', justifyContent: 'center' }}>
          {perfiles.map(perfil => (
            <div
              key={perfil.id}
              onClick={() => onSeleccionarPerfil(perfil)}
              className="tarjeta-recibo"
              style={{ cursor: 'pointer', width: '160px', borderTop: `4px solid ${perfil.avatar_color}` }}
            >
              <div style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 600 }}>
                {perfil.nombre}
              </div>
              {perfil.descripcion && (
                <div style={{ fontSize: '12px', color: 'var(--ink-soft)', marginTop: '4px' }}>
                  {perfil.descripcion}
                </div>
              )}
            </div>
          ))}
        </div>
      </main>

      <button
        onClick={() => setPanelAbierto(v => !v)}
        title="Gestionar perfiles"
        style={{
          position: 'fixed', bottom: '32px', right: '32px',
          width: '56px', height: '56px', borderRadius: '50%',
          background: 'var(--ink)', color: 'var(--paper)', border: 'none',
          fontSize: '26px', lineHeight: '56px', padding: 0,
          boxShadow: 'var(--shadow-card)'
        }}
      >
        {panelAbierto ? '×' : '+'}
      </button>

      {panelAbierto && (
        <div
          className="tarjeta-recibo"
          style={{ position: 'fixed', bottom: '100px', right: '32px', width: '280px', zIndex: 10 }}
        >
          <h3 style={{ fontSize: '15px', marginBottom: '12px' }}>Nuevo perfil</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginBottom: '20px' }}>
            <input placeholder="Nombre" value={nombreNuevo} onChange={e => setNombreNuevo(e.target.value)} />
            <input placeholder="Descripción (opcional)" value={descripcionNueva} onChange={e => setDescripcionNueva(e.target.value)} />
            <button onClick={crearPerfil} style={{ background: 'var(--ink)', color: 'var(--paper)', border: 'none' }}>
              Crear
            </button>
          </div>

          <h3 style={{ fontSize: '15px', marginBottom: '8px', borderTop: '1px solid var(--line)', paddingTop: '14px' }}>
            Eliminar perfil
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {perfiles.map(perfil => (
              <div key={perfil.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px' }}>
                <span>{perfil.nombre}</span>
                <button
                  onClick={() => eliminarPerfil(perfil)}
                  style={{ background: 'transparent', border: 'none', color: 'var(--stamp)', fontSize: '12px', padding: '2px 6px' }}
                >
                  Eliminar
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default PaginaPerfiles