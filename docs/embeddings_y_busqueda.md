# Proceso de Embeddings y Búsqueda Híbrida

El motor de búsqueda de este proyecto no funciona simplemente buscando coincidencias exactas de texto (como el clásico `LIKE %texto%` de SQL o el operador `.contains()` de MongoDB). El objetivo es que el motor **comprenda** la intención del texto.

## 1. El Problema de la Búsqueda Vectorial Pura
Si utilizamos solamente un modelo de lenguaje denso y un usuario busca *"angustia"*, la IA matemáticamente posicionará en la parte superior los versículos que hablen de *"tristeza"*, *"dolor"* o *"sufrimiento"*, aunque la palabra exacta "angustia" no aparezca ni una sola vez. **Esto es el objetivo deseado de la búsqueda semántica.**

Sin embargo, los modelos densos tienen un talón de Aquiles: **los nombres propios y las entidades raras**. Si el usuario busca *"Nabucodonosor"* o *"Jerusalén"*, los vectores densos suelen fallar miserablemente porque esos nombres propios no tienen un significado semántico rico detrás de ellos (solo son etiquetas conceptuales estáticas). El modelo podría devolver cualquier otro rey, ciudad u objeto antiguo con una semántica parecida.

## 2. La Solución: Búsqueda Híbrida (Dense + Sparse)
Para ofrecer resultados perfectos en ambos mundos, configuramos a Qdrant para trabajar con dos motores de búsqueda que operan de forma simultánea.

### A. Motor Denso (Significado Conceptual)
- **Modelo Utilizado:** `intfloat/multilingual-e5-small`.
- **Propósito:** Entender el contexto general, las paráfrasis y los conceptos implícitos.
- **Asimetría:** Este modelo es "Asimétrico". Fue entrenado bajo la premisa de que las preguntas son cortas y directas, pero los textos de la base de datos son narrativos. Por esto, requiere estrictamente que se le añada el prefijo `passage: ` a la información indexada, y `query: ` a lo que teclea el usuario.

### B. Motor Disperso / Sparse (Léxico Exacto / BM25)
- **Modelo Utilizado:** `Qdrant/bm25` (implementado vía la librería ultra-rápida `fastembed`).
- **Propósito:** Actúa como un índice invertido estadístico. Evalúa la frecuencia del término (TF-IDF). Si el usuario busca "Nabucodonosor", este motor penalizará todo lo que no contenga esa palabra exacta y le dará un puntaje altísimo a los versículos que sí la tengan.

## 3. Enriquecimiento Semántico mediante Máquina de Estados
Indexar un solo versículo de la Biblia es muy peligroso a nivel de IA debido a la pérdida de contexto (fragmentación conceptual).
Por ejemplo, un versículo que diga: *"Y él le dijo: no vayas"*. La IA no tiene idea de quién es "él", a quién le habla, o de qué trata el capítulo, y terminará indexando el vector de forma errática.

**La Solución:** 
El script de poblamiento (`populate_db.py`) lee el JSON estructurado de forma secuencial, y utilizando variables locales a modo de "Máquina de Estados", *recuerda* constantemente el último subtítulo (`heading1`) y etiqueta narrativa (`label`) que cruzó antes de llegar al versículo actual.

Al momento de solicitarle al modelo E5 que cree el vector (embedding), no le enviamos solo el versículo, sino un *Prompt Inyectado*:
> `passage: Libro: Génesis. Tema: La Creación. Texto: En el principio creó Dios los cielos y la tierra.`

Gracias a esto, el vector final hereda la carga semántica de su título y contexto narrativo.

## 4. Fusión de Resultados (Reciprocal Rank Fusion - RRF)
Una vez que el usuario hace clic en "Buscar", FastAPI lanza la consulta.
- Se genera un vector denso para capturar la "idea" del usuario.
- Se genera un vector disperso (sparse) para capturar las "palabras" del usuario.

Enviamos ambos vectores a Qdrant mediante el mecanismo de **Prefetch**. Qdrant ejecuta las dos búsquedas internamente y, de forma nativa, cruza y califica las dos listas resultantes utilizando el algoritmo **RRF (Reciprocal Rank Fusion)**. 

La respuesta final de Qdrant eleva a las primeras posiciones aquellos versículos que satisfacen *tanto la coincidencia de palabras exactas como el fondo conceptual de la pregunta*.
