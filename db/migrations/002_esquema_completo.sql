CREATE TABLE tipos_ticket (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE comercios (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    cadena TEXT,
    direccion TEXT,
    nif TEXT,
    tipo_ticket_id INTEGER REFERENCES tipos_ticket(id),
    UNIQUE(nombre, direccion)
);

CREATE TABLE categorias_producto (
    id SERIAL PRIMARY KEY,
    nombre TEXT UNIQUE NOT NULL
);

CREATE TABLE productos (
    id SERIAL PRIMARY KEY,
    nombre_normalizado TEXT UNIQUE NOT NULL,
    categoria_id INTEGER REFERENCES categorias_producto(id),
    unidad_medida TEXT,
    embedding VECTOR(1536)
);

CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    comercio_id INTEGER REFERENCES comercios(id),
    tipo_ticket_id INTEGER REFERENCES tipos_ticket(id),
    fecha DATE,
    total NUMERIC(10, 2),
    imagen_path TEXT,
    estado TEXT DEFAULT 'pendiente_revision',
    motivo_revision TEXT,
    atributos JSONB,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT now()
);

CREATE TABLE lineas_ticket (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES tickets(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    descripcion_original TEXT NOT NULL,
    cantidad NUMERIC(10, 2),
    precio_unitario NUMERIC(10, 2),
    iva NUMERIC(5, 2),
    subtotal NUMERIC(10, 2)
);

CREATE INDEX idx_lineas_ticket_id ON lineas_ticket(ticket_id);
CREATE INDEX idx_lineas_producto_id ON lineas_ticket(producto_id);
CREATE INDEX idx_tickets_comercio ON tickets(comercio_id);
CREATE INDEX idx_tickets_atributos ON tickets USING GIN (atributos);

INSERT INTO tipos_ticket (nombre) VALUES
('supermercado'), ('gasolinera'), ('restaurante'), ('cafeteria'), ('farmacia'),
('suministros_luz'), ('suministros_agua'), ('suministros_gas'), ('telecomunicaciones'),
('ropa_moda'), ('electronica'), ('hogar_decoracion'), ('ocio_entretenimiento'),
('transporte'), ('salud_bienestar'), ('seguros'), ('educacion'), ('otro');

INSERT INTO categorias_producto (nombre) VALUES
('lacteos'), ('carne'), ('pescado_marisco'), ('fruta'), ('verdura_hortaliza'),
('panaderia_bolleria'), ('cereales_pasta_arroz'), ('conservas'), ('congelados'),
('salsas_condimentos'), ('snacks_dulces'), ('alimentacion_infantil'),
('alimentacion_general'), ('bebidas_alcoholicas'), ('bebidas_no_alcoholicas'),
('higiene_personal'), ('limpieza_hogar'), ('combustible'), ('restauracion'),
('ropa_calzado'), ('electronica_tecnologia'), ('salud_farmacia'),
('papeleria_oficina'), ('mascotas'), ('hogar_menaje'), ('ocio_cultura'), ('otros');