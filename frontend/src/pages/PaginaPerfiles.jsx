import { useState, useEffect } from 'react'
import { obtenerPerfiles } from '../services/api.js'

function PaginaPerfiles({ onSeleccionarPerfil }) {
  const [perfiles, setPerfiles] = useState([])

  useEffect(() => {
    obtenerPerfiles().then(setPerfiles)
  }, [])

  return (
    <div>
      <h1>¿Quién eres?</h1>
      <div style={{ display: 'flex', gap: '20px' }}>
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
              fontSize: '16px'
            }}
          >
            {perfil.nombre}
          </button>
        ))}
      </div>
    </div>
  )
}

export default PaginaPerfiles