import { useState } from 'react'
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

const COLORES = ['#4A90D9', '#D9784A', '#4AD98F', '#D94A7A', '#A94AD9']

function PaginaSQL({ onVolver }) {
  const [sql, setSql] = useState(CONSULTAS_PREDEFINIDAS['Gasto por categoría'])
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState(null)
  const [columnaX, setColumnaX] = useState('')
  const [columnaY, setColumnaY] = useState('')
  const [tipoGrafico, setTipoGrafico] = useState('bar')

  async function ejecutar() {
    setError(null)
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
  }

  function exportarCSV() {
    if (!resultado) return
    const encabezado = resultado.columnas.join(',')
    const filas = resultado.filas.map(fila =>
      fila.map(valor => `"${String(valor).replace(/"/g, '""')}"`).join(',')
    )
    const contenidoCSV = [encabezado, ...filas].join('\n')

    const blob = new Blob([contenidoCSV], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const enlace = document.createElement('a')
    enlace.href = url
    enlace.download = `consulta_${Date.now()}.csv`
    enlace.click()
    URL.revokeObjectURL(url)
  }

  const datosGrafico = resultado
    ? resultado.filas.map(fila => {
        const obj = {}
        resultado.columnas.forEach((col, i) => { obj[col] = fila[i] })
        return obj
      })
    : []

  return (
    <div>
      <button onClick={onVolver}>← Volver al menú</button>
      <h1>Consola SQL (solo lectura)</h1>

      <div>
        {Object.keys(CONSULTAS_PREDEFINIDAS).map(nombre => (
          <button key={nombre} onClick={() => setSql(CONSULTAS_PREDEFINIDAS[nombre])}>
            {nombre}
          </button>
        ))}
      </div>

      <textarea rows={6} style={{ width: '100%', marginTop: '10px' }} value={sql} onChange={e => setSql(e.target.value)} />
      <button onClick={ejecutar}>Ejecutar</button>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {resultado && (
        <>
          <table border="1" style={{ marginTop: '20px' }}>
            <thead>
              <tr>{resultado.columnas.map(c => <th key={c}>{c}</th>)}</tr>
            </thead>
            <tbody>
              {resultado.filas.map((fila, i) => (
                <tr key={i}>{fila.map((valor, j) => <td key={j}>{String(valor)}</td>)}</tr>
              ))}
            </tbody>
          </table>

          <button onClick={exportarCSV} style={{ marginTop: '10px' }}>Exportar a CSV</button>

          <h3>Graficar</h3>
          <label>Tipo: </label>
          <select value={tipoGrafico} onChange={e => setTipoGrafico(e.target.value)}>
            <option value="bar">Barras</option>
            <option value="line">Líneas</option>
            <option value="pie">Tarta</option>
          </select>
          <label> Eje/Categoría: </label>
          <select value={columnaX} onChange={e => setColumnaX(e.target.value)}>
            {resultado.columnas.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
          <label> Valor: </label>
          <select value={columnaY} onChange={e => setColumnaY(e.target.value)}>
            {resultado.columnas.map(c => <option key={c} value={c}>{c}</option>)}
          </select>

          <ResponsiveContainer width="100%" height={300}>
            {tipoGrafico === 'bar' && (
              <BarChart data={datosGrafico}>
                <XAxis dataKey={columnaX} />
                <YAxis />
                <Tooltip />
                <Bar dataKey={columnaY} fill="#4A90D9" />
              </BarChart>
            )}
            {tipoGrafico === 'line' && (
              <LineChart data={datosGrafico}>
                <XAxis dataKey={columnaX} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey={columnaY} stroke="#4A90D9" />
              </LineChart>
            )}
            {tipoGrafico === 'pie' && (
              <PieChart>
                <Pie data={datosGrafico} dataKey={columnaY} nameKey={columnaX} outerRadius={100} label>
                  {datosGrafico.map((_, i) => <Cell key={i} fill={COLORES[i % COLORES.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            )}
          </ResponsiveContainer>
        </>
      )}
    </div>
  )
}

export default PaginaSQL