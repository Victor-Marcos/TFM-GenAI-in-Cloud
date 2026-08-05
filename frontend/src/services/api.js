const API_URL = 'http://localhost:8000'

export async function obtenerPerfiles() {
  const respuesta = await fetch(`${API_URL}/perfiles`)
  return respuesta.json()
}

export async function obtenerTickets(perfilId) {
  const respuesta = await fetch(`${API_URL}/tickets?perfil_id=${perfilId}`)
  return respuesta.json()
}

export async function subirTicket(archivo, perfilId) {
  const formData = new FormData()
  formData.append('archivo', archivo)
  const respuesta = await fetch(`${API_URL}/tickets?perfil_id=${perfilId}`, {
    method: 'POST',
    body: formData
  })
  return respuesta.json()
}