function PaginaMenu({ perfil, onIrA, onCambiarPerfil }) {
  return (
    <div>
      <h1>Hola, {perfil.nombre}</h1>
      <div style={{ display: 'flex', gap: '20px', flexDirection: 'column', maxWidth: '300px' }}>
        <button onClick={() => onIrA('carga')}>Subir tickets</button>
        <button onClick={() => onIrA('pendientes')}>Revisar pendientes</button>
        <button onClick={() => onIrA('chat')}>Analizar con el agente</button>
        <button onClick={() => onIrA('dashboard')}>Ver dashboard</button>
        <button onClick={() => onIrA('sql')}>Consola SQL</button>
      </div>
      <button onClick={onCambiarPerfil} style={{ marginTop: '20px' }}>Cambiar de perfil</button>
    </div>
  )
}

export default PaginaMenu