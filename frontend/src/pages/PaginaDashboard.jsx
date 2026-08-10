import { useState, useEffect } from 'react'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'

const API_URL = 'http://localhost:8000'

function TarjetaKPI({ etiqueta, valor }) {
  return (
    <div className="tarjeta-recibo" style={{ minWidth: '160px', flex: 1 }}>
      <div style={{ fontSize: '12px', color: 'var(--ink-soft)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {etiqueta}
      </div>
      <div className="mono" style={{ fontSize: '26px', fontWeight: 600, marginTop: '6px' }}>
        {valor}
      </div>
    </div>
  )
}

function SeccionResumen({ perfil }) {
  const [resumen, setResumen] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/resumen?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setResumen)
  }, [])

  if (!resumen) return <p>Cargando...</p>

  return (
    <>
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '20px' }}>
        <TarjetaKPI etiqueta="Gasto total" valor={`${resumen.gasto_total.toFixed(2)}€`} />
        <TarjetaKPI etiqueta="Tickets" valor={resumen.total_tickets} />
        <TarjetaKPI etiqueta="Ticket medio" valor={`${resumen.ticket_medio}€`} />
        <TarjetaKPI etiqueta="Comercios" valor={resumen.comercios_distintos} />
        <TarjetaKPI etiqueta="Productos distintos" valor={resumen.productos_distintos} />
      </div>

      <div className="tarjeta-recibo" style={{ maxWidth: '320px' }}>
        <h3 style={{ fontSize: '14px', marginBottom: '10px' }}>Tickets por estado</h3>
        {Object.entries(resumen.tickets_por_estado).map(([estado, cantidad]) => (
          <div key={estado} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
            <span>{estado}</span>
            <span className="mono">{cantidad}</span>
          </div>
        ))}
      </div>
    </>
  )
}

function SeccionEvolucion({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/evolucion?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  const signoVariacion = datos.comparativa.variacion_pct >= 0 ? '+' : ''

  return (
    <>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <TarjetaKPI etiqueta="Mes anterior" valor={`${datos.comparativa.mes_anterior.toFixed(2)}€`} />
        <TarjetaKPI etiqueta="Mes actual" valor={`${datos.comparativa.mes_actual.toFixed(2)}€`} />
        <TarjetaKPI
          etiqueta="Variación"
          valor={`${signoVariacion}${datos.comparativa.variacion_pct}%`}
        />
      </div>

      <div className="tarjeta-recibo" style={{ marginBottom: '20px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>Gasto por mes</h3>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={datos.por_mes}>
            <XAxis dataKey="mes" stroke="var(--ink-soft)" />
            <YAxis stroke="var(--ink-soft)" />
            <Tooltip />
            <Line type="monotone" dataKey="total" stroke="#3A6351" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="tarjeta-recibo">
        <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>Gasto por día de la semana</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={datos.por_dia_semana}>
            <XAxis dataKey="dia" stroke="var(--ink-soft)" />
            <YAxis stroke="var(--ink-soft)" />
            <Tooltip />
            <Bar dataKey="total" fill="#C1440E" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}

function PaginaDashboard({ perfil, onVolver }) {
  const [pestana, setPestana] = useState('resumen')

  const pestanas = [
    { id: 'resumen', etiqueta: 'Resumen' },
    { id: 'evolucion', etiqueta: 'Evolución' },
    { id: 'categorias', etiqueta: 'Categorías' },
    { id: 'comercios', etiqueta: 'Comercios' },
    { id: 'productos', etiqueta: 'Productos' },
    { id: 'patrones', etiqueta: 'Patrones' },
    { id: 'tipos', etiqueta: 'Tipos' },
    { id: 'calidad', etiqueta: 'Calidad del sistema' },
  ]

  return (
    <div className="contenedor-ancho">
      <button onClick={onVolver} style={{ marginBottom: '20px' }}>← Volver al menú</button>
      <h1 style={{ marginBottom: '16px' }}>Dashboard</h1>

      <div style={{ display: 'flex', gap: '4px', marginBottom: '20px', borderBottom: '2px solid var(--line)', flexWrap: 'wrap' }}>
        {pestanas.map(p => (
          <button
            key={p.id}
            onClick={() => setPestana(p.id)}
            style={{
              border: 'none', borderRadius: '0', background: 'transparent',
              borderBottom: pestana === p.id ? '2px solid var(--ink)' : '2px solid transparent',
              marginBottom: '-2px', fontWeight: pestana === p.id ? 600 : 400, fontSize: '13px'
            }}
          >
            {p.etiqueta}
          </button>
        ))}
      </div>

      {pestana === 'resumen' && <SeccionResumen perfil={perfil} />}
      {pestana === 'evolucion' && <SeccionEvolucion perfil={perfil} />}
      {pestana === 'categorias' && <SeccionCategorias perfil={perfil} />}
      {pestana === 'comercios' && <SeccionComercios perfil={perfil} />}
      {pestana === 'productos' && <SeccionProductos perfil={perfil} />}
      {pestana === 'patrones' && <SeccionPatrones perfil={perfil} />}
      {pestana === 'tipos' && <SeccionTipos perfil={perfil} />}
      {pestana === 'calidad' && <SeccionCalidad perfil={perfil} />}
    </div>
  )
}

export default PaginaDashboard

function SeccionCategorias({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/categorias?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <>
      <div className="tarjeta-recibo" style={{ marginBottom: '20px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>Gasto por categoría</h3>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={datos.gasto_por_categoria} layout="vertical" margin={{ left: 100 }}>
            <XAxis type="number" stroke="var(--ink-soft)" />
            <YAxis type="category" dataKey="categoria" width={140} tick={{ fontSize: 11 }} stroke="var(--ink-soft)" />
            <Tooltip />
            <Bar dataKey="total" fill="#C1440E" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="tarjeta-recibo">
        <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Ticket medio por categoría</h3>
        {datos.ticket_medio_por_categoria.slice(0, 10).map(c => (
          <div key={c.categoria} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
            <span>{c.categoria}</span>
            <span className="mono">{c.media}€</span>
          </div>
        ))}
      </div>
    </>
  )
}

function SeccionComercios({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/comercios?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <div className="tarjeta-recibo" style={{ overflowX: 'auto' }}>
      <table className="mono" style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th style={{ textAlign: 'left', padding: '6px' }}>Comercio</th>
            <th style={{ padding: '6px' }}>Gasto</th>
            <th style={{ padding: '6px' }}>Visitas</th>
            <th style={{ padding: '6px' }}>Ticket medio</th>
          </tr>
        </thead>
        <tbody>
          {datos.map(c => (
            <tr key={c.comercio}>
              <td style={{ padding: '6px', borderBottom: '1px solid var(--line)' }}>{c.comercio}</td>
              <td style={{ padding: '6px', borderBottom: '1px solid var(--line)', textAlign: 'right' }}>{c.gasto.toFixed(2)}€</td>
              <td style={{ padding: '6px', borderBottom: '1px solid var(--line)', textAlign: 'right' }}>{c.visitas}</td>
              <td style={{ padding: '6px', borderBottom: '1px solid var(--line)', textAlign: 'right' }}>{c.ticket_medio}€</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SeccionProductos({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/productos?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
      <div className="tarjeta-recibo" style={{ flex: 1, minWidth: '320px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Más comprados (frecuencia)</h3>
        {datos.top_frecuencia.map(p => (
          <div key={p.producto} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '5px' }}>
            <span>{p.producto}</span>
            <span className="mono">{p.veces}×</span>
          </div>
        ))}
      </div>
      <div className="tarjeta-recibo" style={{ flex: 1, minWidth: '320px' }}>
        <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Mayor gasto total</h3>
        {datos.top_gasto.map(p => (
          <div key={p.producto} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '5px' }}>
            <span>{p.producto}</span>
            <span className="mono">{p.gasto_total.toFixed(2)}€</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function SeccionPatrones({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/patrones?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <div className="tarjeta-recibo">
      <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Productos que compras juntos</h3>
      {datos.productos_juntos.map((p, i) => (
        <div key={i} style={{ fontSize: '13px', marginBottom: '6px' }}>
          <span>{p.producto_a}</span> + <span>{p.producto_b}</span>
          <span className="mono" style={{ color: 'var(--ink-soft)' }}> ({p.veces_juntos} veces)</span>
        </div>
      ))}
    </div>
  )
}

function SeccionTipos({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/tipos?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <div className="tarjeta-recibo">
      <h3 style={{ fontSize: '15px', marginBottom: '14px' }}>Gasto por tipo de ticket</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={datos.por_tipo}>
          <XAxis dataKey="tipo" stroke="var(--ink-soft)" tick={{ fontSize: 11 }} />
          <YAxis stroke="var(--ink-soft)" />
          <Tooltip />
          <Bar dataKey="total" fill="#3A6351" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function SeccionCalidad({ perfil }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/dashboard/calidad?perfil_id=${perfil.id}`)
      .then(r => r.json())
      .then(setDatos)
  }, [])

  if (!datos) return <p>Cargando...</p>

  return (
    <>
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <TarjetaKPI etiqueta="Total tickets" valor={datos.total_tickets} />
        <TarjetaKPI etiqueta="Auto-validados" valor={datos.auto_validados} />
        <TarjetaKPI etiqueta="% auto-validado" valor={`${datos.porcentaje_auto_validado}%`} />
      </div>
      <div className="tarjeta-recibo">
        <h3 style={{ fontSize: '15px', marginBottom: '10px' }}>Motivos de revisión más frecuentes</h3>
        {datos.motivos_frecuentes.map(m => (
          <div key={m.motivo} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '4px' }}>
            <span>{m.motivo}</span>
            <span className="mono">{m.veces}</span>
          </div>
        ))}
      </div>
    </>
  )
}