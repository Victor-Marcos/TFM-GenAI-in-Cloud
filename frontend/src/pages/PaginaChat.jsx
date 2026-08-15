import { useState, useRef, useEffect } from 'react'

const API_URL = 'http://localhost:8000'

function PaginaChat({ perfil, onVolver }) {
  const [mensajes, setMensajes] = useState([])
  const [pregunta, setPregunta] = useState('')
  const [enviando, setEnviando] = useState(false)
  const finRef = useRef(null)

  useEffect(() => {
    finRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [mensajes])

  async function enviarPregunta() {
    if (!pregunta.trim() || enviando) return

    const preguntaActual = pregunta
    const historialActual = mensajes
    setMensajes(previos => [...previos, { autor: 'usuario', texto: preguntaActual }])
    setPregunta('')
    setEnviando(true)

    try {
      const respuesta = await fetch(`${API_URL}/chat?perfil_id=${perfil.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pregunta: preguntaActual, historial: historialActual })
      })
      const datos = await respuesta.json()
      setMensajes(previos => [...previos, { autor: 'agente', texto: datos.respuesta }])
    } catch (error) {
      setMensajes(previos => [...previos, { autor: 'agente', texto: 'Ha ocurrido un error al procesar tu pregunta.' }])
    } finally {
      setEnviando(false)
    }
  }

  function manejarTecla(evento) {
    if (evento.key === 'Enter' && !evento.shiftKey) {
      evento.preventDefault()
      enviarPregunta()
    }
  }

  return (
    <div className="contenedor-app" style={{ display: 'flex', flexDirection: 'column', height: '85vh' }}>
      <button onClick={onVolver} style={{ marginBottom: '20px', alignSelf: 'flex-start' }}>← Volver al menú</button>
      <h1 style={{ marginBottom: '16px' }}>Pregúntale a tus datos</h1>

      <div style={{ flex: 1, overflowY: 'auto', marginBottom: '16px' }}>
        {mensajes.length === 0 && (
          <p style={{ color: 'var(--ink-soft)', fontSize: '14px' }}>
            Prueba a preguntar cosas como "¿en qué gasto más?", "¿qué compro con más frecuencia?" o "¿qué tan fiable es el sistema?".
          </p>
        )}

        {mensajes.map((m, i) => (
          <div
            key={i}
            className="tarjeta-recibo"
            style={{
              maxWidth: '75%',
              marginLeft: m.autor === 'usuario' ? 'auto' : '0',
              background: m.autor === 'usuario' ? 'var(--ink)' : 'var(--paper-raised)',
              color: m.autor === 'usuario' ? 'var(--paper)' : 'var(--ink)',
              whiteSpace: 'pre-wrap',
              fontSize: '14px'
            }}
          >
            {m.texto}
          </div>
        ))}

        {enviando && (
          <div className="tarjeta-recibo" style={{ maxWidth: '75%', fontSize: '14px', color: 'var(--ink-soft)' }}>
            Pensando...
          </div>
        )}

        <div ref={finRef} />
      </div>

      <div style={{ display: 'flex', gap: '10px' }}>
        <textarea
          value={pregunta}
          onChange={e => setPregunta(e.target.value)}
          onKeyDown={manejarTecla}
          placeholder="Escribe tu pregunta..."
          rows={2}
          style={{ flex: 1, resize: 'none' }}
        />
        <button
          onClick={enviarPregunta}
          disabled={enviando || !pregunta.trim()}
          style={{ background: 'var(--ink)', color: 'var(--paper)', border: 'none' }}
        >
          Enviar
        </button>
      </div>
    </div>
  )
}

export default PaginaChat