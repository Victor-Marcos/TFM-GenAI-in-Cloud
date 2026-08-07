import { useState } from 'react'
import './App.css'
import PaginaPerfiles from './pages/PaginaPerfiles.jsx'
import PaginaMenu from './pages/PaginaMenu.jsx'
import PaginaCargaDatos from './pages/PaginaCargaDatos.jsx'
import PaginaPendientes from './pages/PaginaPendientes.jsx'
import PaginaSQL from './pages/PaginaSQL.jsx'

function App() {
  const [perfilActivo, setPerfilActivo] = useState(null)
  const [pantalla, setPantalla] = useState('menu')

  if (!perfilActivo) {
    return <PaginaPerfiles onSeleccionarPerfil={setPerfilActivo} />
  }

  if (pantalla === 'menu') {
    return (
      <PaginaMenu
        perfil={perfilActivo}
        onIrA={setPantalla}
        onCambiarPerfil={() => setPerfilActivo(null)}
      />
    )
  }

  if (pantalla === 'carga') {
    return <PaginaCargaDatos perfil={perfilActivo} onVolver={() => setPantalla('menu')} />
  }

  if (pantalla === 'pendientes') {
    return <PaginaPendientes perfil={perfilActivo} onVolver={() => setPantalla('menu')} />
  }
  
  if (pantalla === 'sql') {
  return <PaginaSQL onVolver={() => setPantalla('menu')} />
}

  return <p>Pantalla "{pantalla}" todavía no construida</p>
}

export default App