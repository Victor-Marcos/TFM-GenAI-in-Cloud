import { useState, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function PaginaPerfiles({ onSeleccionarPerfil }) {
  const [perfiles, setPerfiles] = useState([])
  const [nombreNuevo, setNombreNuevo] = useState('')
  const [descripcionNueva, setDescripcionNueva] = useState('')

  useEffect(() => {
    cargar()
  }, [])

  function cargar() {
    fetch(`${API_URL}/perfiles`)
      .then(r => r.json())
      .then(setPerfiles)
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

  return (
    <div>
      <h1>¿Quién eres?</h1>

      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
        {perfiles.map(perfil => (
          <button
            key={perfil.id}
            onClick={() => onSeleccionarPerfil(perfil)}
            style={{
              backgroundColor: perfil.avatar_color,
              padding: '20px',
              borderRadius: '8px',
              color: 'white',
              border: 'none',
              cursor: 'pointer',
              fontSize: '16px',
              textAlign: 'left'
            }}
          >
            <div>{perfil.nombre}</div>
            {perfil.descripcion && <div style={{ fontSize: '12px', opacity: 0.8 }}>{perfil.descripcion}</div>}
          </button>
        ))}
      </div>

      <h3>Crear nuevo perfil</h3>
      <input
        placeholder="Nombre"
        value={nombreNuevo}
        onChange={e => setNombreNuevo(e.target.value)}
      />
      <input
        placeholder="Descripción (opcional)"
        value={descripcionNueva}
        onChange={e => setDescripcionNueva(e.target.value)}
      />
      <button onClick={crearPerfil}>Crear</button>
    </div>
  )
}

export default PaginaPerfiles