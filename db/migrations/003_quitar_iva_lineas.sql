-- El IVA se gestiona a nivel de ticket (tickets.atributos->desglose_iva),
-- no por linea de producto, ya que los tickets reales no suelen desglosarlo asi.
ALTER TABLE lineas_ticket DROP COLUMN IF EXISTS iva;
