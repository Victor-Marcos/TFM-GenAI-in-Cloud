import { useState, useRef } from 'react'
import './App.css'
import PaginaPerfiles from './pages/PaginaPerfiles.jsx'
import PaginaMenu from './pages/PaginaMenu.jsx'
import PaginaCargaDatos from './pages/PaginaCargaDatos.jsx'
import PaginaPendientes from './pages/PaginaPendientes.jsx'
import PaginaSQL from './pages/PaginaSQL.jsx'
import PaginaDashboard from './pages/PaginaDashboard.jsx'
import PaginaChat from './pages/PaginaChat.jsx'

function App() {
  const [perfilActivo, setPerfilActivo] = useState(null)
  const [pantalla, setPantalla] = useState('menu')

  const [ficheros, setFicheros] = useState([])
  const [resultadosCarga, setResultadosCarga] = useState([])
  const [procesando, setProcesando] = useState(false)
  const [progreso, setProgreso] = useState({ actual: 0, total: 0 })
  const cancelarRef = useRef(false)

  if (!perfilActivo) {
    return <PaginaPerfiles onSeleccionarPerfil={setPerfilActivo} />
  }

  if (pantalla === 'menu') {
    return (
      <PaginaMenu
        onIrA={setPantalla}
        onCambiarPerfil={() => setPerfilActivo(null)}
      />
    )
  }

  if (pantalla === 'carga') {
    return (
      <PaginaCargaDatos
        perfil={perfilActivo}
        onVolver={() => setPantalla('menu')}
        ficheros={ficheros}
        setFicheros={setFicheros}
        resultados={resultadosCarga}
        setResultados={setResultadosCarga}
        procesando={procesando}
        setProcesando={setProcesando}
        cancelarRef={cancelarRef}
        progreso={progreso}
        setProgreso={setProgreso}
      />
    )
  }

  if (pantalla === 'pendientes') {
    return <PaginaPendientes perfil={perfilActivo} onVolver={() => setPantalla('menu')} />
  }

  if (pantalla === 'sql') {
    return <PaginaSQL onVolver={() => setPantalla('menu')} />
  }
  if (pantalla === 'dashboard') {
    return <PaginaDashboard perfil={perfilActivo} onVolver={() => setPantalla('menu')} />
  }

  if (pantalla === 'chat') {
    return <PaginaChat perfil={perfilActivo} onVolver={() => setPantalla('menu')} />
  }

  return <p>Pantalla "{pantalla}" todavía no construida</p>
}

export default App