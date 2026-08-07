import { useState, useEffect, useRef } from 'react'
import mermaid from 'mermaid'

const API_URL = 'http://localhost:8000'

function construirDiagrama(esquema) {
  let texto = 'erDiagram\n'
  for (const [tabla, columnas] of Object.entries(esquema.tablas)) {
    texto += `  ${tabla} {\n`
    columnas.forEach(c => { texto += `    ${c.tipo.replace(/\s/g, '_')} ${c.columna}\n` })
    texto += `  }\n`
  }
  esquema.relaciones.forEach(r => {
    texto += `  ${r.tabla_destino} ||--o{ ${r.tabla_origen} : "${r.columna_origen}"\n`
  })
  return texto
}

function PaginaEsquema({ onVolver }) {
  const [svg, setSvg] = useState('')
  const contenedorRef = useRef(null)

  useEffect(() => {
    fetch(`${API_URL}/esquema`)
      .then(r => r.json())
      .then(async esquema => {
        mermaid.initialize({ startOnLoad: false, theme: 'neutral' })
        const definicion = construirDiagrama(esquema)
        const { svg } = await mermaid.render('diagrama-erd', definicion)
        setSvg(svg)
      })
  }, [])

  return (
    <div className="contenedor-ancho">
      <button onClick={onVolver} style={{ marginBottom: '20px' }}>← Volver al menú</button>
      <h1 style={{ marginBottom: '20px' }}>Estructura de la base de datos</h1>
      <div className="tarjeta-recibo" style={{ overflow: 'auto' }} dangerouslySetInnerHTML={{ __html: svg }} />
    </div>
  )
}

export default PaginaEsquema