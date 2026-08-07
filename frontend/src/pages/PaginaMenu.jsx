function PaginaMenu({ onIrA, onCambiarPerfil }) {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '20px' }}>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', width: '260px' }}>
        <button onClick={() => onIrA('carga')}>Subir tickets</button>
        <button onClick={() => onIrA('pendientes')}>Revisar pendientes</button>
        <button onClick={() => onIrA('sql')}>Consola SQL</button>
        <button onClick={() => onIrA('chat')}>Analizar con el agente</button>
        <button onClick={() => onIrA('dashboard')}>Ver dashboard</button>
      </div>

      <button
        onClick={onCambiarPerfil}
        style={{ background: 'transparent', border: 'none', color: 'var(--ink-soft)', fontSize: '13px' }}
      >
        Cambiar de perfil
      </button>
    </div>
  )
}

export default PaginaMenu