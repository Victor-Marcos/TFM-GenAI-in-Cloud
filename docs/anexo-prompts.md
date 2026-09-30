# Ejemplos de prompts utilizados

Anexo al Trabajo Fin de Máster “Implementación de un ecosistema de
Agentes de IA en Entorno Cloud para el procesamiento de tickets y
generación dinámica de analíticas descriptivas”.

Víctor Marcos Garrachón · Máster en Big Data y Ciencia de Datos ·
Universidad Internacional de Valencia (VIU)

Las herramientas y los modelos utilizados se detallan en la declaración
sobre IA generativa incluida en la memoria. Este anexo recoge ejemplos
representativos de las interacciones mantenidas, ordenados según su
propósito.

Cada entrada muestra el prompt original, un extracto de la respuesta
obtenida y, sobre todo, el uso real que se le dio en el proyecto.

# Diseño del sistema

## Arquitectura del sistema multiagente

**Prompt**

> *Quiero crear un sistema de agentes haciendo uso de langraph, pero
> quiero crear varios nodos, no solo un agente. Quiero que el sistema no
> se excesivamente simple, quiero algo realizar algo complejo por
> aprender, pero que a la vez sea útil. ¿Qué arquitectura me recomiendas
> hacer?*

**Respuesta obtenida**

Propuso una arquitectura en cadena, con los nodos ejecutándose de forma
secuencial.

**Uso dado:** se descartó por no ajustarse al objetivo. El autor pidió
una alternativa basada en un orquestador: «Está bien, pero eso es en
cadena, no es un sistema de nodos. Quiero algo un poco más elaborado,
donde utilice también un orquestador que decida qué hacer». De esa
segunda propuesta nació la idea del diseño final: un nodo orquestador y
cinco rutas de especialista. El uso de un agente verificador y el
reparto de herramientas entre los especialistas lo definió el autor.

# 2. Verificación de los datos de la memoria

## 2.1 Comprobar si el sistema respondía con datos reales.

**Prompt**

*\[comprobación de la respuesta del agente a la pregunta «cuánto me he
gastado en carne en julio» contra una consulta SQL directa\]: El prompt
consistió en la pregunta «cuánto me he gastado en carne en julio», en la
respuesta del sistema de agentes y en el log del sistema de agentes para
observar la herramienta de la que estaba haciendo uso.*

**Respuesta obtenida**

El agente había añadido por su cuenta un filtro de año que la pregunta
no pedía:

AND t.fecha \>= '2024-07-01' AND t.fecha \<= '2024-07-31'

Al ejecutar la consulta sin esa restricción, el gasto real en esa
categoría durante el mes de julio ascendía a 74,86 €, repartidos entre
los años 2020, 2023, 2024 y 2026.

**Uso dado:** se corrigieron las instrucciones del especialista para
prohibir la asunción de un año implícito cuando el usuario no lo
especifica, y para obligar al uso de EXTRACT(MONTH FROM fecha) en lugar
de comparaciones textuales. Tras la corrección, el sistema pasó a
devolver el total correcto con el desglose por años.

# 3. Depuración del sistema

## 3.1 La aplicación no mostraba los perfiles

**Prompt**

> *he cargado el sistema en local, pero no me salen los perfiles*

**Respuesta obtenida**

Propuso una secuencia de comprobaciones ordenada de más a menos
probable: contenido de la base de datos, respuesta directa del backend,
código de la petición en el navegador y URL compilada en el frontend.
Tras descartar las tres primeras, identificó la causa:

> \$ docker compose up backend
>
> Error response from daemon: ports are not available:
>
> exposing port TCP 127.0.0.1:8000
>
> \$ ss -ltnp \| grep :8000
>
> LISTEN 127.0.0.1:8000 users:(("uvicorn",pid=119944))

**Uso dado:** un proceso uvicorn lanzado a mano desde el entorno virtual
ocupaba el puerto 8000 e impedía arrancar el contenedor del backend. Se
resolvió cerrando ese proceso. Las comprobaciones intermedias las
ejecutó el autor, que fue descartando hipótesis hasta llegar a la causa.

## 3.2 Conflicto de dependencias al construir la imagen

**Prompt**

> *\[salida del error de pip durante docker compose build\]*

**Respuesta obtenida**

Identificó el conflicto entre la versión fijada y el rango exigido por
otra dependencia:

> ERROR: Cannot install -r requirements.txt (line 3) and
>
> google-genai==1.15.0 because these package versions have
>
> conflicting dependencies.
>
> The user requested google-genai==1.15.0
>
> langchain-google-genai 4.4.0 depends on google-genai
>
> \<3.0.0 and \>=2.20.0

**Uso dado:** se corrigió liberando la restricción de versión. La
versión conflictiva la había indicado la propia herramienta en una
interacción anterior y no era válida; el error se detectó al construir
la imagen.

# 4. Redacción y composición del documento

## 4.1 Traducción del resumen al inglés

**Prompt**

*\[resumen en castellano pegado\] Tradúcelo tal cual está al inglés*

**Respuesta obtenida**

Devolvió la traducción del *abstract* manteniendo la estructura y la
terminología técnica del original.

**Uso dado:** el autor la revisó y ajustó varios términos para que
coincidieran con los empleados en el cuerpo del documento. Previamente
había preguntado si, tras completar el despliegue en la nube, convenía
modificar algo del resumen original; a raíz de esa consulta se actualizó
el texto en castellano antes de traducirlo.

**Uso dado:** se añadió al preámbulo, con lo que quedaron corregidos
todos los listados del documento.

## 4.2 Diagrama Gantt que desbordaba os márgenes

**Prompt**

*\[código del diagrama con pgfgantt y captura mostrando el
desbordamiento\]*

**Respuesta obtenida**

Señaló dos problemas: que el diagrama excedía el ancho de la caja de
texto y que el eje temporal con fechas completas resultaba ilegible al
comprimirlo. Propuso escalar la figura y sustituir el eje de fechas por
una numeración de semanas:

\resizebox{\textwidth}{!}{%

\begin{ganttchart}\[...\]{1}{20}

\gantttitle{Semanas}{20} \\

...

\end{ganttchart}

}

**Uso dado:** se aplicó al cronograma del capítulo de metodología. La
planificación representada (fases, duraciones y solapamientos) es la
seguida realmente por el autor durante el desarrollo.

## 4.3 Comillas y caracteres especiales en castellano

**Prompt**

*¿Cómo puedo poner "c sin que me lo convierta en ç?*

**Respuesta obtenida**

Explicó uso de c{}' para eviar la aparición del carácter ç.

**Uso dado:** se aplicó al cronograma del capítulo de metodología. La
planificación representada (fases, duraciones y solapamientos) es la
seguida realmente por el autor durante el desarrollo.

**Uso dado:** se sustituyeron todos los caracteres ç del documento por
“c, con lo que se resolvió el problema.

## 4.4 Ampliación del marco teórico

**Prompt**

*Quiero contar un poco más de teoría, redacta en total una cara más.
\[Se adjuntó la redacción actual del apartado de teoría\]*

**Respuesta obtenida**

Amplió el apartado con la evolución desde los modelos secuenciales hasta
la arquitectura Transformer y los modelos multimodales actuales.

**Uso dado:** se incorporó tras la revisión del autor, que detectó y
corrigió una afirmación técnica errónea en el texto devuelto (ver
apartado 6.1 de este anexo).
