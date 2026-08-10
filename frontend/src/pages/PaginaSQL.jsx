import { useState, useEffect } from 'react'
import * as XLSX from 'xlsx'
import mermaid from 'mermaid'
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const API_URL = 'http://localhost:8000'

const CONSULTAS_PREDEFINIDAS = {
  'Gasto por categoría': `SELECT cp.nombre AS categoria, SUM(lt.subtotal) AS total
FROM lineas_ticket lt
JOIN productos p ON lt.producto_id = p.id
JOIN categorias_producto cp ON p.categoria_id = cp.id
GROUP BY cp.nombre
ORDER BY total DESC`,
  'Gasto por comercio': `SELECT c.nombre AS comercio, SUM(t.total) AS total
FROM tickets t
JOIN comercios c ON t.comercio_id = c.id
GROUP BY c.nombre
ORDER BY total DESC`,
  'Evolución mensual': `SELECT to_char(fecha, 'YYYY-MM') AS mes, SUM(total) AS total
FROM tickets
GROUP BY mes
ORDER BY mes`
}

const COLORES = ['#C1440E', '#3A6351', '#B08968', '#5B6660', '#8A9B68']

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

function PaginaSQL({ onVolver }) {
  const [pestana, setPestana] = useState('consulta')
  const [sql, setSql] = useState(CONSULTAS_PREDEFINIDAS['Gasto por categoría'])
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)
  const [columnaX, setColumnaX] = useState('')
  const [columnaY, setColumnaY] = useState('')
  const [tipoGrafico, setTipoGrafico] = useState('bar')
  const [maximizado, setMaximizado] = useState(false)
  const [cargando, setCargando] = useState(false)
  const [svgEsquema, setSvgEsquema] = useState('')

  useEffect(() => {
    if (pestana === 'esquema' && !svgEsquema) {
      fetch(`${API_URL}/esquema`)
        .then(r => r.json())
        .then(async esquema => {
          mermaid.initialize({ startOnLoad: false, theme: 'neutral' })
          const definicion = construirDiagrama(esquema)
          const { svg } = await mermaid.render('diagrama-erd', definicion)
          setSvgEsquema(svg)
        })
    }
  }, [pestana])

  async function ejecutar() {
  setError(null)
  setCargando(true)
  try {
    const respuesta = await fetch(`${API_URL}/consulta-sql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql })
    })
    if (!respuesta.ok) {
      const detalle = await respuesta.json()
      setError(detalle.detail)
      setResultado(null)
      return
    }
    const datos = await respuesta.json()
    setResultado(datos)
    setColumnaX(datos.columnas[0] || '')
    setColumnaY(datos.columnas[1] || '')
  } finally {
    setCargando(false)
  }
}

  function exportarExcel() {
    if (!resultado) return
    const hoja = XLSX.utils.aoa_to_sheet([resultado.columnas, ...resultado.filas])
    const libro = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(libro, hoja, 'Resultado')
    XLSX.writeFile(libro, `consulta_${Date.now()}.xlsx`)
  }

  const datosGrafico = resultado
    ? resultado.filas.map(fila => {
        const obj = {}
        resultado.columnas.forEach((col, i) => { obj[col] = fila[i] })
        return obj
      })
    : []

  return (
    <div className="contenedor-ancho">
      <button onClick={onVolver} style={{ marginBottom: '20px' }}>← Volver al menú</button>
      <h1 style={{ marginBottom: '16px' }}>Base de datos</h1>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '2px solid var(--line)' }}>
        <button
          onClick={() => setPestana('consulta')}
          style={{
            border: 'none', borderRadius: '0', background: 'transparent',
            borderBottom: pestana === 'consulta' ? '2px solid var(--ink)' : '2px solid transparent',
            marginBottom: '-2px', fontWeight: pestana === 'consulta' ? 600 : 400
          }}
        >
          Consulta SQL
        </button>
        <button
          onClick={() => setPestana('esquema')}
          style={{
            border: 'none', borderRadius: '0', background: 'transparent',
            borderBottom: pestana === 'esquema' ? '2px solid var(--ink)' : '2px solid transparent',
            marginBottom: '-2px', fontWeight: pestana === 'esquema' ? 600 : 400
          }}
        >
          Estructura de la BBDD
        </button>
      </div>

      {pestana === 'esquema' && (
        <div className="tarjeta-recibo" style={{ overflow: 'auto' }} dangerouslySetInnerHTML={{ __html: svgEsquema }} />
      )}

      {pestana === 'consulta' && (
        <>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', flexWrap: 'wrap' }}>
            {Object.keys(CONSULTAS_PREDEFINIDAS).map(nombre => (
              <button key={nombre} onClick={() => setSql(CONSULTAS_PREDEFINIDAS[nombre])} style={{ fontSize: '13px' }}>
                {nombre}
              </button>
            ))}
          </div>

          <div
            className="tarjeta-recibo"
            style={maximizado
              ? { position: 'fixed', inset: '24px', zIndex: 50, display: 'flex', flexDirection: 'column', margin: 0 }
              : { display: 'flex', flexDirection: 'column' }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <span className="mono" style={{ fontSize: '12px', color: 'var(--ink-soft)', letterSpacing: '0.06em' }}>
                SQL · SOLO LECTURA
              </span>
              <button onClick={() => setMaximizado(m => !m)} style={{ padding: '4px 10px', fontSize: '12px' }}>
                {maximizado ? 'Minimizar' : 'Maximizar'}
              </button>
            </div>
            <textarea
              value={sql}
              onChange={e => setSql(e.target.value)}
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '14px',
                lineHeight: 1.6,
                width: '100%',
                flex: maximizado ? 1 : 'none',
                minHeight: maximizado ? undefined : '180px',
                resize: maximizado ? 'none' : 'vertical'
              }}
            />
            <div style={{ marginTop: '10px' }}>
              <button onClick={ejecutar} disabled={cargando} style={{ background: 'var(--ink)', color: 'var(--paper)', border: 'none' }}>
              {cargando ? 'Ejecutando...' : 'Ejecutar'}
              </button>
            </div>
          </div>

          {maximizado && (
            <div
              onClick={() => setMaximizado(false)}
              style={{ position: 'fixed', inset: 0, background: 'rgba(31,36,33,0.35)', zIndex: 40 }}
            />
          )}

          {error && <p style={{ color: 'var(--stamp)', marginTop: '16px' }}>{error}</p>}

          {resultado && !maximizado && (
            <>
              <div className="tarjeta-recibo" style={{ overflowX: 'auto', marginTop: '20px' }}>
                <table className="mono" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr>{resultado.columnas.map(c => (
                      <th key={c} style={{ textAlign: 'left', borderBottom: '2px solid var(--line)', padding: '6px 10px' }}>{c}</th>
                    ))}</tr>
                  </thead>
                  <tbody>
                    {resultado.filas.map((fila, i) => (
                      <tr key={i}>{fila.map((valor, j) => (
                        <td key={j} style={{ borderBottom: '1px solid var(--line)', padding: '6px 10px' }}>{String(valor)}</td>
                      ))}</tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <button onClick={exportarExcel} style={{ marginTop: '12px' }}>Exportar a Excel</button>

              <div className="tarjeta-recibo" style={{ marginTop: '20px' }}>
                <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>Graficar</h3>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '16px', flexWrap: 'wrap' }}>
                  <label>Tipo:
                    <select value={tipoGrafico} onChange={e => setTipoGrafico(e.target.value)} style={{ marginLeft: '6px' }}>
                      <option value="bar">Barras</option>
                      <option value="line">Líneas</option>
                      <option value="pie">Tarta</option>
                    </select>
                  </label>
                  <label>Eje/Categoría:
                    <select value={columnaX} onChange={e => setColumnaX(e.target.value)} style={{ marginLeft: '6px' }}>
                      {resultado.columnas.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </label>
                  <label>Valor:
                    <select value={columnaY} onChange={e => setColumnaY(e.target.value)} style={{ marginLeft: '6px' }}>
                      {resultado.columnas.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </label>
                </div>

                <ResponsiveContainer width="100%" height={360}>
                  {tipoGrafico === 'bar' && (
                    <BarChart data={datosGrafico}>
                      <XAxis dataKey={columnaX} stroke="var(--ink-soft)" />
                      <YAxis stroke="var(--ink-soft)" />
                      <Tooltip />
                      <Bar dataKey={columnaY} fill="#C1440E" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  )}
                  {tipoGrafico === 'line' && (
                    <LineChart data={datosGrafico}>
                      <XAxis dataKey={columnaX} stroke="var(--ink-soft)" />
                      <YAxis stroke="var(--ink-soft)" />
                      <Tooltip />
                      <Line type="monotone" dataKey={columnaY} stroke="#3A6351" strokeWidth={2} />
                    </LineChart>
                  )}
                  {tipoGrafico === 'pie' && (
                    <PieChart>
                      <Pie data={datosGrafico} dataKey={columnaY} nameKey={columnaX} outerRadius={120} label>
                        {datosGrafico.map((_, i) => <Cell key={i} fill={COLORES[i % COLORES.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  )}
                </ResponsiveContainer>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default PaginaSQL