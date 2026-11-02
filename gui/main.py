
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import os
import sys
import threading

# CONFIGURACION DE LA VENTANA

ventana = tk.Tk()
ventana.title("Proyecto - Planeacion Curricular")
ventana.geometry("1920x1080")
ventana.minsize(900, 600)

# Colores de la interfaz
AZUL_OSCURO = "#172554"
AZUL = "#2563EB"
FONDO = "#F1F5F9"
BLANCO = "#FFFFFF"
TEXTO = "#1E293B"
VERDE = "#15803D"

ventana.configure(bg=FONDO)

# DATOS DE C A PYTHON

# CARGA DE DATOS DE C


# Cargar las materias utilizando las funciones del programa C
def cargar_materias_c():
    global BIBLIOTECA
    # Buscar los archivos junto a main.py
    carpeta = os.path.dirname(os.path.abspath(__file__))
    nombre_dll = "cursos.dll" if sys.platform.startswith("win") else "libcursos.so"
    ruta_dll = os.path.join(carpeta, nombre_dll)
    ruta_archivo = os.path.join(carpeta, "cursos.txt")

    # Si no hay cursos.txt junto a main.py, se usa el del proyecto
    if not os.path.exists(ruta_archivo):
        alterna = os.path.join(carpeta, "..", "quicksort", "cursos.txt")
        if os.path.exists(alterna):
            ruta_archivo = os.path.normpath(alterna)

    # Cargar la biblioteca de C
    biblioteca = ctypes.CDLL(ruta_dll)

    # Definir los tipos de datos de las funciones
    biblioteca.cargar_cursos.argtypes = [ctypes.c_char_p]
    biblioteca.cargar_cursos.restype = ctypes.c_int

    biblioteca.obtener_total_cursos.restype = ctypes.c_int

    biblioteca.obtener_nombre.argtypes = [ctypes.c_int]
    biblioteca.obtener_nombre.restype = ctypes.c_char_p

    biblioteca.obtener_creditos.argtypes = [ctypes.c_int]
    biblioteca.obtener_creditos.restype = ctypes.c_int

    biblioteca.obtener_semestre.argtypes = [ctypes.c_int]
    biblioteca.obtener_semestre.restype = ctypes.c_int

    biblioteca.obtener_dificultad.argtypes = [ctypes.c_int]
    biblioteca.obtener_dificultad.restype = ctypes.c_int

    biblioteca.obtener_num_prerequisitos.argtypes = [ctypes.c_int]
    biblioteca.obtener_num_prerequisitos.restype = ctypes.c_int

    biblioteca.obtener_prerequisito.argtypes = [
        ctypes.c_int, ctypes.c_int
    ]
    biblioteca.obtener_prerequisito.restype = ctypes.c_int

    biblioteca.liberar_cursos.argtypes = []
    biblioteca.liberar_cursos.restype = None

    # Funciones del puente para ordenar, elegibles, planes, etc.
    configurar_funciones_extra(biblioteca)

    # Pedir a C que lea el archivo
    total = biblioteca.cargar_cursos(os.fsencode(ruta_archivo))

    if total <= 0:
        raise RuntimeError(
            "C no pudo cargar las materias de cursos.txt"
        )

    materias_cargadas = []

    try:
        for i in range(total):
            # Obtener el nombre y convertirlo a texto de Python
            nombre_bytes = biblioteca.obtener_nombre(i)
            nombre = nombre_bytes.decode("utf-8")

            creditos = biblioteca.obtener_creditos(i)
            semestre = biblioteca.obtener_semestre(i)
            dificultad = biblioteca.obtener_dificultad(i)

            # Obtener los índices de los prerrequisitos
            cantidad = biblioteca.obtener_num_prerequisitos(i)
            prerequisitos = []

            for j in range(cantidad):
                prerequisitos.append(
                    biblioteca.obtener_prerequisito(i, j)
                )

            # Mantener el formato de tu interfaz actual:
            # (nombre, créditos, semestre, dificultad, prerrequisitos)
            materias_cargadas.append((
                nombre,
                creditos,
                semestre,
                dificultad,
                prerequisitos
            ))

    except Exception:
        # Si algo falla, se libera la memoria reservada en C
        biblioteca.liberar_cursos()
        raise

    # La malla se queda cargada en C: las demas pantallas la siguen usando
    BIBLIOTECA = biblioteca
    return materias_cargadas


# Biblioteca de C ya cargada (la usan todas las pantallas)
BIBLIOTECA = None


def configurar_funciones_extra(biblioteca):
    """Define los tipos de las funciones del puente que no son de carga."""
    arreglo_int = ctypes.POINTER(ctypes.c_int)

    biblioteca.ordenar_cursos.argtypes = [
        ctypes.c_int, ctypes.c_int, arreglo_int
    ]
    biblioteca.ordenar_cursos.restype = ctypes.c_int

    biblioteca.calcular_elegibles.argtypes = [ctypes.c_char_p, arreglo_int]
    biblioteca.calcular_elegibles.restype = ctypes.c_int

    biblioteca.validar_indices_malla.argtypes = []
    biblioteca.validar_indices_malla.restype = ctypes.c_int

    biblioteca.buscar_ciclos.argtypes = []
    biblioteca.buscar_ciclos.restype = ctypes.c_int

    biblioteca.obtener_ciclo.argtypes = [
        ctypes.c_int, arreglo_int, ctypes.c_int
    ]
    biblioteca.obtener_ciclo.restype = ctypes.c_int

    biblioteca.plan_sugerido.argtypes = [
        ctypes.c_int, ctypes.c_int, arreglo_int
    ]
    biblioteca.plan_sugerido.restype = ctypes.c_int

    biblioteca.plan_voraz.argtypes = [
        ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ctypes.c_char_p, arreglo_int
    ]
    biblioteca.plan_voraz.restype = ctypes.c_int

    biblioteca.plan_bt.argtypes = [
        ctypes.c_char_p, ctypes.c_int, ctypes.c_int, ctypes.c_longlong,
        arreglo_int, ctypes.POINTER(ctypes.c_longlong), arreglo_int
    ]
    biblioteca.plan_bt.restype = ctypes.c_int


# Cargar las materias reales desde el programa C
error_carga = None
try:
    materias = cargar_materias_c()
    print("Materias cargadas:", len(materias))
except (OSError, RuntimeError, UnicodeDecodeError) as error:
    materias = []
    error_carga = str(error)
    print("Error al cargar las materias:", error)

materias_aprobadas = []

# FUNCIONES QUE USAN EL CODIGO EN C

# Topes del plan sugerido (los mismos del programa de consola)
MAX_CREDITOS_SEMESTRE = 50
MAX_DIFICULTAD_SEMESTRE = 38

# Limite de pasos del backtracking para que la busqueda no sea interminable
LIMITE_PASOS_BACKTRACKING = 3000000

# Campo que entiende el quicksort de C para cada criterio de la pantalla
CAMPOS_ORDENAMIENTO = {
    "Creditos": 0,
    "Dificultad": 1,
    "Semestre sugerido": 2,
    "Nombre": 3
}


def hay_biblioteca():
    """Indica si la malla se cargo correctamente desde C."""
    return BIBLIOTECA is not None and len(materias) > 0


def nuevo_arreglo_c(tamano):
    """Arreglo de enteros que C puede llenar."""
    return (ctypes.c_int * max(tamano, 1))()


def nombres_prerrequisitos(indices):
    """Convierte los indices de prerrequisitos en nombres legibles."""
    nombres = [
        materias[i][0] for i in indices
        if 0 <= i < len(materias)
    ]
    return ", ".join(nombres) if nombres else "Ninguno"


def fila_materia(indice):
    """Fila de la tabla (con nombres de prerrequisitos) de una materia."""
    nombre, creditos, semestre, dificultad, prerrequisitos = materias[indice]
    return (
        nombre,
        creditos,
        semestre,
        dificultad,
        nombres_prerrequisitos(prerrequisitos)
    )


def construir_aprobadas():
    """Un byte por materia (1 = aprobada), en el orden de la malla."""
    aprobadas = set(materias_aprobadas)
    return bytes(1 if m[0] in aprobadas else 0 for m in materias)


def creditos_por_semestre(asignacion):
    """Suma los creditos de cada semestre de un plan (0 = aprobada)."""
    totales = {}
    for indice, semestre in enumerate(asignacion):
        if semestre > 0:
            totales[semestre] = (
                totales.get(semestre, 0) + materias[indice][1]
            )
    return totales


def ordenar_materias_c(campo, descendente=False):
    """Quicksort en C. Devuelve los indices de las materias ya ordenadas."""
    if not hay_biblioteca():
        return []
    salida = nuevo_arreglo_c(len(materias))
    total = BIBLIOTECA.ordenar_cursos(
        campo, 1 if descendente else 0, salida
    )
    if total < 0:
        raise RuntimeError("C no pudo ordenar las materias")
    return [salida[k] for k in range(total)]


def elegibles_c():
    """Indices de las materias que se pueden cursar con el historial."""
    if not hay_biblioteca():
        return []
    salida = nuevo_arreglo_c(len(materias))
    total = BIBLIOTECA.calcular_elegibles(construir_aprobadas(), salida)
    return [salida[k] for k in range(total)]


def validar_malla_c():
    """Devuelve (indices_invalidos, ciclos). Cada ciclo es una lista de
    indices donde cada materia requiere a la siguiente."""
    if not hay_biblioteca():
        return 0, []
    invalidos = BIBLIOTECA.validar_indices_malla()
    total = BIBLIOTECA.buscar_ciclos()
    ciclos = []
    for k in range(max(min(total, 16), 0)):
        nodos = nuevo_arreglo_c(128)
        largo = BIBLIOTECA.obtener_ciclo(k, nodos, 128)
        ciclos.append([nodos[j] for j in range(largo)])
    return invalidos, ciclos


def plan_sugerido_c(max_creditos, max_dificultad):
    """Semestre sugerido (quicksort + restricciones). Devuelve
    (semestres, asignacion) o (-1, []) si no se pudo calcular."""
    if not hay_biblioteca():
        return -1, []
    asignacion = nuevo_arreglo_c(len(materias))
    semestres = BIBLIOTECA.plan_sugerido(
        max_creditos, max_dificultad, asignacion
    )
    return semestres, [asignacion[i] for i in range(len(materias))]


def plan_voraz_c(criterio, max_creditos):
    """Seleccion voraz de las materias pendientes. criterio: 0 = materias
    que desbloquea, 1 = solo creditos. Devuelve (semestres, asignacion)."""
    if not hay_biblioteca():
        return -1, []
    asignacion = nuevo_arreglo_c(len(materias))
    semestres = BIBLIOTECA.plan_voraz(
        criterio, max_creditos, 0, construir_aprobadas(), asignacion
    )
    return semestres, [asignacion[i] for i in range(len(materias))]


def plan_backtracking_c(max_creditos, aprobadas):
    """Backtracking en C. Se puede llamar desde otro hilo."""
    resultado = {
        "codigo": -1, "semestres": 0, "truncado": 0,
        "optimo": 0, "pasos": 0, "asignacion": []
    }
    if not hay_biblioteca():
        return resultado
    asignacion = nuevo_arreglo_c(len(materias))
    pasos = (ctypes.c_longlong * 1)()
    info = nuevo_arreglo_c(4)
    resultado["codigo"] = BIBLIOTECA.plan_bt(
        aprobadas, max_creditos, 0, LIMITE_PASOS_BACKTRACKING,
        asignacion, pasos, info
    )
    resultado["semestres"] = info[0]
    resultado["truncado"] = info[1]
    resultado["optimo"] = info[2]
    resultado["pasos"] = pasos[0]
    resultado["asignacion"] = [asignacion[i] for i in range(len(materias))]
    return resultado

# ESTILO DE TABLAS Y BOTONES

estilo = ttk.Style()
estilo.theme_use("clam")

estilo.configure(
    "Treeview",
    background=BLANCO,
    foreground=TEXTO,
    rowheight=32,
    fieldbackground=BLANCO,
    font=("Segoe UI", 10)
)

estilo.configure(
    "Treeview.Heading",
    font=("Segoe UI", 10, "bold"),
    background="#E2E8F0",
    foreground=TEXTO
)

estilo.configure(
    "TCombobox",
    padding=5
)



# ESTRUCTURA PRINCIPAL

# Menu lateral
menu_lateral = tk.Frame(
    ventana,
    bg=AZUL_OSCURO,
    width=230
)
menu_lateral.pack(side="left", fill="y")
menu_lateral.pack_propagate(False)

# Area donde cambia el contenido
contenido = tk.Frame(ventana, bg=FONDO)
contenido.pack(side="right", fill="both", expand=True)

# FUNCIONES AUXILIARES

def limpiar_contenido():
    """Elimina la pantalla actual."""
    for elemento in contenido.winfo_children():
        elemento.destroy()


def crear_titulo(titulo, descripcion):
    """Muestra el titulo y la descripcion de una pantalla."""
    encabezado = tk.Frame(contenido, bg=FONDO)
    encabezado.pack(fill="x", padx=30, pady=(25, 15))

    tk.Label(
        encabezado,
        text=titulo,
        font=("Segoe UI", 22, "bold"),
        bg=FONDO,
        fg=TEXTO
    ).pack(anchor="w")

    tk.Label(
        encabezado,
        text=descripcion,
        font=("Segoe UI", 10),
        bg=FONDO,
        fg="#64748B"
    ).pack(anchor="w", pady=(5, 0))


def crear_tabla(columnas, filas):
    """Crea una tabla para mostrar datos."""
    marco = tk.Frame(contenido, bg=BLANCO)
    marco.pack(fill="both", expand=True, padx=30, pady=(0, 25))

    tabla = ttk.Treeview(
        marco,
        columns=columnas,
        show="headings"
    )

    for columna in columnas:
        tabla.heading(columna, text=columna)
        tabla.column(columna, width=130, anchor="w")

    for fila in filas:
        tabla.insert("", "end", values=fila)

    tabla.pack(fill="both", expand=True, padx=10, pady=10)
    return tabla


def crear_tarjeta(padre, titulo, valor, descripcion):
    """Crea una tarjeta de resumen."""
    tarjeta = tk.Frame(
        padre,
        bg=BLANCO,
        highlightbackground="#E2E8F0",
        highlightthickness=1
    )

    tk.Label(
        tarjeta,
        text=titulo,
        bg=BLANCO,
        fg="#64748B",
        font=("Segoe UI", 10)
    ).pack(anchor="w", padx=15, pady=(15, 5))

    tk.Label(
        tarjeta,
        text=valor,
        bg=BLANCO,
        fg=AZUL,
        font=("Segoe UI", 24, "bold")
    ).pack(anchor="w", padx=15)

    tk.Label(
        tarjeta,
        text=descripcion,
        bg=BLANCO,
        fg=TEXTO,
        font=("Segoe UI", 9)
    ).pack(anchor="w", padx=15, pady=(5, 15))

    return tarjeta


def mensaje_pendiente(funcion):
    """Muestra una seccion visual que aun no esta conectada."""
    limpiar_contenido()
    crear_titulo(funcion, "Prototipo visual: calculos aun no conectados.")

    panel = tk.Frame(contenido, bg=BLANCO)
    panel.pack(fill="x", padx=30, pady=10)

    tk.Label(
        panel,
        text="Esta seccion esta preparada para el siguiente paso.",
        bg=BLANCO,
        fg=TEXTO,
        font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=20, pady=(20, 8))

    tk.Label(
        panel,
        text=(
            "Por ahora mostraremos datos de ejemplo. "
            "Despues conectaremos esta pantalla con los algoritmos en C."
        ),
        bg=BLANCO,
        fg="#64748B",
        font=("Segoe UI", 10),
        wraplength=650,
        justify="left"
    ).pack(anchor="w", padx=20, pady=(0, 20))



def crear_contenedor_desplazable(padre, altura=260):
    # Creamos un panel que tendrá una altura limitada.
    # Así, la lista no empujará el resto de la interfaz hacia abajo.
    contenedor = tk.Frame(padre, bg=BLANCO, height=altura)

    # Evitamos que el panel cambie de tamaño según la cantidad de materias.
    contenedor.pack_propagate(False)

    # El panel ocupará el ancho disponible.
    contenedor.pack(fill="x", padx=15, pady=5)

    # Creamos el área donde se dibujará la lista de materias.
    canvas = tk.Canvas(
        contenedor,
        bg=BLANCO,
        highlightthickness=0
    )
    canvas.pack(side="left", fill="both", expand=True)

    # Creamos una barra de desplazamiento vertical.
    barra = ttk.Scrollbar(
        contenedor,
        orient="vertical",
        command=canvas.yview
    )
    barra.pack(side="right", fill="y")

    # Conectamos la barra con el área desplazable.
    canvas.configure(yscrollcommand=barra.set)

    # Este marco contendrá todas las casillas de materias.
    lista_interna = tk.Frame(canvas, bg=BLANCO)

    # Insertamos el marco dentro del Canvas.
    id_lista = canvas.create_window(
        (0, 0),
        window=lista_interna,
        anchor="nw"
    )

    # Actualizamos el área desplazable cuando cambie la lista.
    def actualizar_area(evento):
        canvas.configure(scrollregion=canvas.bbox("all"))

    lista_interna.bind("<Configure>", actualizar_area)

    # Ajustamos el ancho de la lista al ancho visible del Canvas.
    def ajustar_ancho(evento):
        canvas.itemconfigure(id_lista, width=evento.width)

    canvas.bind("<Configure>", ajustar_ancho)

    # Permitimos usar la rueda del ratón cuando este se encuentra
    # sobre el área de la lista.
    def usar_rueda(evento):
        canvas.yview_scroll(
            int(-evento.delta / 120),
            "units"
        )

    canvas.bind("<MouseWheel>", usar_rueda)

    # Devolvemos el marco donde colocaremos las casillas.
    return lista_interna




# PANTALLA DE INICIO

def mostrar_inicio():
    limpiar_contenido()

    crear_titulo(
        "Panel principal",
        "Resumen de la malla curricular y el avance academico."
    )

    tarjetas = tk.Frame(contenido, bg=FONDO)
    tarjetas.pack(fill="x", padx=30, pady=10)

    datos_tarjetas = [
        ("Materias", str(len(materias)), "En la malla curricular"),
        ("Aprobadas", str(len(materias_aprobadas)), "Materias registradas"),
        ("Pendientes", str(len(materias) - len(materias_aprobadas)),
         "Por acreditar"),
    ]

    for titulo, valor, descripcion in datos_tarjetas:
        tarjeta = crear_tarjeta(
            tarjetas, titulo, valor, descripcion
        )
        tarjeta.pack(
            side="left",
            fill="both",
            expand=True,
            padx=(0, 12)
        )

    panel = tk.Frame(contenido, bg=BLANCO)
    panel.pack(fill="x", padx=30, pady=20)

    tk.Label(
        panel,
        text="Accesos rapidos",
        bg=BLANCO,
        fg=TEXTO,
        font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=20, pady=(18, 10))

    botones = [
        ("Consultar malla curricular", mostrar_malla),
        ("Consultar materias elegibles", mostrar_elegibles),
        ("Ver carga academica", mostrar_carga),
        ("Consultar planeacion", mostrar_planeacion),
    ]

    for texto, funcion in botones:
        tk.Button(
            panel,
            text=texto,
            command=funcion,
            bg="#EFF6FF",
            fg=AZUL,
            activebackground="#DBEAFE",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 10),
            anchor="w",
            padx=15,
            pady=10
        ).pack(fill="x", padx=20, pady=4)

    tk.Label(
        contenido,
        text="Datos cargados desde cursos.txt con el codigo en C.",
        bg=FONDO,
        fg="#64748B",
        font=("Segoe UI", 9)
    ).pack(anchor="w", padx=30, pady=5)

# MALLA CURRICULAR


def mostrar_malla():
    # Limpiamos el contenido anterior para mostrar esta pantalla.
    limpiar_contenido()

    # Mostramos el título y la descripción de la sección.
    crear_titulo(
        "Malla curricular",
        "Consulta las materias de tu carrera y filtra la información."
    )

    # Creamos un panel para colocar los controles de búsqueda.
    panel_filtros = tk.Frame(contenido, bg=BLANCO)
    panel_filtros.pack(fill="x", padx=30, pady=10)

    # Variable que guarda el texto que el usuario quiere buscar.
    texto_busqueda = tk.StringVar()

    # Variable que guarda el semestre seleccionado.
    semestre_seleccionado = tk.StringVar(value="Todos")

    # Etiqueta que indica qué debe escribirse en el campo.
    etiqueta_busqueda = tk.Label(
        panel_filtros,
        text="Buscar materia:",
        bg=BLANCO,
        fg=TEXTO,
        font=("Arial", 10, "bold")
    )
    etiqueta_busqueda.pack(side="left", padx=(10, 5), pady=15)

    # Campo donde el usuario escribe el nombre de una materia.
    entrada_busqueda = ttk.Entry(
        panel_filtros,
        textvariable=texto_busqueda,
        width=25
    )
    entrada_busqueda.pack(side="left", padx=5, pady=15)

    # Etiqueta del filtro por semestre.
    etiqueta_semestre = tk.Label(
        panel_filtros,
        text="Semestre:",
        bg=BLANCO,
        fg=TEXTO,
        font=("Arial", 10, "bold")
    )
    etiqueta_semestre.pack(side="left", padx=(15, 5), pady=15)

    # Obtenemos los semestres que existen actualmente en las materias.
    semestres_disponibles = sorted({
        str(materia[2]) for materia in materias
    }, key=int)

    # Agregamos la opción "Todos" para quitar el filtro de semestre.
    opciones_semestres = ["Todos"] + semestres_disponibles

    # Lista desplegable para seleccionar un semestre.
    filtro_semestre = ttk.Combobox(
        panel_filtros,
        textvariable=semestre_seleccionado,
        values=opciones_semestres,
        state="readonly",
        width=10
    )
    filtro_semestre.pack(side="left", padx=5, pady=15)

    # Creamos el panel que contendrá la tabla de materias.
    panel_tabla = tk.Frame(contenido, bg=BLANCO)
    panel_tabla.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(5, 25)
    )

    # Definimos las columnas que aparecerán en la tabla.
    columnas = (
        "Materia",
        "Créditos",
        "Semestre",
        "Dificultad",
        "Prerrequisito"
    )

    # Creamos la tabla sin agregar una columna adicional para los identificadores.
    tabla = ttk.Treeview(
        panel_tabla,
        columns=columnas,
        show="headings"
    )

    # Configuramos el nombre visible y el ancho de cada columna.
    tabla.heading("Materia", text="Materia")
    tabla.heading("Créditos", text="Créditos")
    tabla.heading("Semestre", text="Semestre")
    tabla.heading("Dificultad", text="Dificultad")
    tabla.heading("Prerrequisito", text="Prerrequisito")

    tabla.column("Materia", width=220)
    tabla.column("Créditos", width=80, anchor="center")
    tabla.column("Semestre", width=90, anchor="center")
    tabla.column("Dificultad", width=100, anchor="center")
    tabla.column("Prerrequisito", width=200)

    # Colocamos la tabla para que ocupe el espacio disponible.
    tabla.pack(fill="both", expand=True, padx=10, pady=10)

    # Esta función actualiza la tabla según los filtros elegidos.
    def actualizar_tabla():
        # Eliminamos las filas que estaban visibles anteriormente.
        for fila in tabla.get_children():
            tabla.delete(fila)

        # Obtenemos el texto de búsqueda y lo convertimos a minúsculas.
        # Así podemos buscar sin distinguir entre mayúsculas y minúsculas.
        nombre_busqueda = texto_busqueda.get().strip().lower()

        # Leemos el semestre seleccionado en la lista desplegable.
        semestre = semestre_seleccionado.get()

        # Revisamos todas las materias registradas.
        for materia in materias:
            # Extraemos los datos de la materia según su posición en la tupla.
            nombre = materia[0]
            creditos = materia[1]
            numero_semestre = materia[2]
            dificultad = materia[3]
            prerrequisito = nombres_prerrequisitos(materia[4])

            # Comprobamos si el nombre contiene el texto buscado.
            coincide_nombre = nombre_busqueda in nombre.lower()

            # Si se seleccionó "Todos", aceptamos cualquier semestre.
            # De lo contrario, solo aceptamos el semestre elegido.
            coincide_semestre = (
                semestre == "Todos"
                or str(numero_semestre) == semestre
            )

            # Solo mostramos las materias que cumplen ambos filtros.
            if coincide_nombre and coincide_semestre:
                tabla.insert(
                    "",
                    "end",
                    values=(
                        nombre,
                        creditos,
                        numero_semestre,
                        dificultad,
                        prerrequisito
                    )
                )

    # Botón para aplicar la búsqueda y el filtro.
    boton_buscar = tk.Button(
        panel_filtros,
        text="Buscar",
        command=actualizar_tabla,
        bg=AZUL,
        fg="white",
        relief="flat",
        cursor="hand2",
        padx=12
    )
    boton_buscar.pack(side="left", padx=10, pady=15)

    # Esta función limpia los filtros y muestra todas las materias.
    def limpiar_filtros():
        texto_busqueda.set("")
        semestre_seleccionado.set("Todos")
        actualizar_tabla()

    # Botón para restablecer los filtros.
    boton_limpiar = tk.Button(
        panel_filtros,
        text="Limpiar",
        command=limpiar_filtros,
        bg=FONDO,
        fg=TEXTO,
        relief="flat",
        cursor="hand2",
        padx=12
    )
    boton_limpiar.pack(side="left", padx=5, pady=15)

    # Permite iniciar la búsqueda presionando Enter en el campo de texto.
    entrada_busqueda.bind(
        "<Return>",
        lambda evento: actualizar_tabla()
    )

    # Al cambiar el semestre, actualizamos la tabla automáticamente.
    filtro_semestre.bind(
        "<<ComboboxSelected>>",
        lambda evento: actualizar_tabla()
    )

    # Al abrir la pantalla, mostramos todas las materias registradas.
    actualizar_tabla()



# ORDENAMIENTO VISUAL

def mostrar_ordenamiento():
    limpiar_contenido()

    crear_titulo(
        "Ordenar materias",
        "Selecciona un criterio para organizar la tabla."
    )

    panel = tk.Frame(contenido, bg=BLANCO)
    panel.pack(fill="x", padx=30, pady=10)

    tk.Label(
        panel,
        text="Criterio de ordenamiento:",
        bg=BLANCO,
        fg=TEXTO
    ).pack(side="left", padx=15, pady=20)

    criterio = ttk.Combobox(
        panel,
        values=["Creditos", "Dificultad", "Semestre sugerido"],
        state="readonly",
        width=22
    )
    criterio.current(0)
    criterio.pack(side="left", padx=10)

    def ordenar():
        # El ordenamiento lo hace el quicksort escrito en C.
        campo = CAMPOS_ORDENAMIENTO[criterio.get()]

        try:
            orden = ordenar_materias_c(campo)
        except RuntimeError as error:
            messagebox.showerror("Error", str(error))
            return

        for elemento in tabla.get_children():
            tabla.delete(elemento)

        for indice in orden:
            tabla.insert("", "end", values=fila_materia(indice))

    tk.Button(
        panel,
        text="Ordenar",
        command=ordenar,
        bg=AZUL,
        fg=BLANCO,
        relief="flat",
        cursor="hand2",
        padx=15,
        pady=7
    ).pack(side="left", padx=10)

    tabla = crear_tabla(
        ("Materia", "Creditos", "Semestre", "Dificultad", "Prerrequisito"),
        [fila_materia(i) for i in range(len(materias))]
    )


# MATERIAS ELEGIBLES



def mostrar_elegibles():
    # Limpiamos la pantalla anterior antes de construir esta sección.
    limpiar_contenido()

    # Mostramos el encabezado de la pantalla.
    crear_titulo(
        "Materias elegibles",
        "Marca las materias aprobadas para calcular cuáles puedes cursar."
    )

    # Guardamos una variable de selección para cada materia.
    selecciones = {}

    # ---------------------------------------------------------
    # PANEL DE MATERIAS APROBADAS
    # ---------------------------------------------------------

    # Este panel queda directamente dentro del contenido principal.
    panel_materias = tk.Frame(contenido, bg=BLANCO)
    panel_materias.pack(fill="x", padx=30, pady=10)

    # Título del panel de materias.
    tk.Label(
        panel_materias,
        text="Materias aprobadas:",
        font=("Segoe UI", 12, "bold"),
        bg=BLANCO,
        fg=TEXTO
    ).pack(anchor="w", padx=15, pady=(12, 5))

    # Creamos un área desplazable que contiene solamente las casillas.
    # La barra permitirá recorrer la lista si no caben todas las materias.
    area_lista = crear_contenedor_desplazable(
        panel_materias,
        altura=200
    )

    # Creamos una casilla para cada materia del catálogo.
    for materia in materias:
        # Obtenemos el nombre y los créditos de la materia.
        nombre = materia[0]
        creditos = materia[1]

        # Marcamos automáticamente las materias que ya están aprobadas.
        variable = tk.BooleanVar(
            value=nombre in materias_aprobadas
        )

        # Guardamos la variable para leerla cuando se calcule la elegibilidad.
        selecciones[nombre] = variable

        # Creamos la casilla dentro del área desplazable.
        casilla = tk.Checkbutton(
            area_lista,
            text=f"{nombre} ({creditos} créditos)",
            variable=variable,
            bg=BLANCO,
            fg=TEXTO,
            activebackground=BLANCO,
            selectcolor=BLANCO,
            anchor="w",
            font=("Segoe UI", 10)
        )

        # Colocamos la casilla en una fila de la lista.
        casilla.pack(fill="x", padx=15, pady=3)

    # ---------------------------------------------------------
    # PANEL DE RESULTADOS
    # ---------------------------------------------------------

    # IMPORTANTE:
    # La tabla se coloca directamente en contenido, NO en area_lista.
    # Así queda debajo del panel de materias y no dentro de la lista.
    panel_resultados = tk.Frame(contenido, bg=BLANCO)
    panel_resultados.pack(
        fill="both",
        expand=True,
        padx=30,
        pady=(5, 20)
    )

    # Título de la tabla de resultados.
    tk.Label(
        panel_resultados,
        text="Resultado de elegibilidad",
        font=("Segoe UI", 12, "bold"),
        bg=BLANCO,
        fg=TEXTO
    ).pack(anchor="w", padx=15, pady=(12, 5))

    # Definimos las columnas de la tabla.
    columnas = (
        "Materia",
        "Créditos",
        "Prerrequisito",
        "Estado"
    )

    # Creamos la tabla que mostrará las materias pendientes.
    tabla_resultados = ttk.Treeview(
        panel_resultados,
        columns=columnas,
        show="headings",
        height=6
    )

    # Configuramos los encabezados de las columnas.
    for columna in columnas:
        tabla_resultados.heading(columna, text=columna)

    # Ajustamos el ancho de cada columna.
    tabla_resultados.column("Materia", width=250)
    tabla_resultados.column("Créditos", width=90, anchor="center")
    tabla_resultados.column("Prerrequisito", width=220)
    tabla_resultados.column("Estado", width=150)

    # Agregamos una barra para recorrer los resultados si fuera necesario.
    barra_resultados = ttk.Scrollbar(
        panel_resultados,
        orient="vertical",
        command=tabla_resultados.yview
    )

    # Conectamos la tabla con su barra de desplazamiento.
    tabla_resultados.configure(
        yscrollcommand=barra_resultados.set
    )

    # Colocamos la tabla y su barra en el panel.
    tabla_resultados.pack(
        side="left",
        fill="both",
        expand=True,
        padx=(15, 0),
        pady=(5, 15)
    )

    barra_resultados.pack(
        side="right",
        fill="y",
        padx=(0, 15),
        pady=(5, 15)
    )

    # ---------------------------------------------------------
    # CÁLCULO DE ELEGIBILIDAD
    # ---------------------------------------------------------

    def calcular_elegibles(avisar=False):
        # Actualizamos el historial con las casillas seleccionadas.
        # Primero quitamos las selecciones anteriores.
        materias_aprobadas.clear()

        # Guardamos como aprobadas las materias que estén marcadas.
        for nombre, variable in selecciones.items():
            if variable.get():
                materias_aprobadas.append(nombre)

        # Limpiamos los resultados del cálculo anterior.
        for fila in tabla_resultados.get_children():
            tabla_resultados.delete(fila)

        # Avisamos si hay materias aprobadas sin su prerrequisito.
        if avisar:
            incoherencias = []

            for materia in materias:
                if materia[0] not in materias_aprobadas:
                    continue

                for indice in materia[4]:
                    if (0 <= indice < len(materias)
                            and materias[indice][0]
                            not in materias_aprobadas):
                        incoherencias.append(
                            f"{materia[0]} (falta: {materias[indice][0]})"
                        )

            if incoherencias:
                detalle = "\n".join(incoherencias[:8])

                if len(incoherencias) > 8:
                    detalle += f"\n... y {len(incoherencias) - 8} mas"

                messagebox.showwarning(
                    "Historial incoherente",
                    "Hay materias marcadas como aprobadas sin haber "
                    "marcado su prerrequisito:\n\n" + detalle
                )

        # El programa en C calcula cuáles materias se pueden cursar.
        indices_elegibles = set(elegibles_c())

        # Revisamos cada materia del catálogo.
        for indice, materia in enumerate(materias):
            nombre = materia[0]
            creditos = materia[1]
            prerrequisito = nombres_prerrequisitos(materia[4])

            # Si ya está aprobada, no necesita volver a cursarse.
            if nombre in materias_aprobadas:
                continue

            # Elegible: todos sus prerrequisitos están aprobados.
            if indice in indices_elegibles:
                estado = "Elegible"

            # Si no cumple los prerrequisitos, todavía está bloqueada.
            else:
                estado = "No elegible"

            # Mostramos el estado de la materia en la tabla.
            tabla_resultados.insert(
                "",
                "end",
                values=(
                    nombre,
                    creditos,
                    prerrequisito,
                    estado
                )
            )

    # Botón para calcular los resultados después de marcar las casillas.
    boton_calcular = tk.Button(
        panel_materias,
        text="Calcular materias elegibles",
        command=lambda: calcular_elegibles(True),
        bg=AZUL,
        fg=BLANCO,
        relief="flat",
        cursor="hand2",
        font=("Segoe UI", 10),
        padx=12,
        pady=7
    )

    # El botón aparece debajo de la lista desplazable.
    boton_calcular.pack(anchor="w", padx=15, pady=12)

    # Calculamos los resultados al entrar a la pantalla por primera vez.
    calcular_elegibles()




# CARGA ACADEMICA

def mostrar_carga():
    limpiar_contenido()

    crear_titulo(
        "Carga academica",
        "Compara la heuristica voraz con el backtracking segun el "
        "limite de creditos."
    )

    panel = tk.Frame(contenido, bg=BLANCO)
    panel.pack(fill="x", padx=30, pady=10)

    tk.Label(
        panel,
        text="Limite de creditos por semestre:",
        bg=BLANCO,
        fg=TEXTO
    ).pack(side="left", padx=15, pady=20)

    creditos = tk.Spinbox(
        panel,
        from_=1,
        to=60,
        width=6
    )
    creditos.delete(0, "end")
    creditos.insert(0, "50")
    creditos.pack(side="left", padx=10)

    resumen = tk.Label(
        contenido,
        text="",
        bg=FONDO,
        fg="#64748B",
        font=("Segoe UI", 10)
    )
    resumen.pack(anchor="w", padx=30, pady=(0, 5))

    tabla = crear_tabla(
        ("Algoritmo", "Semestres", "Mayor carga (creditos)", "Resultado"),
        []
    )
    tabla.column("Algoritmo", width=300)
    tabla.column("Resultado", width=380)

    def comparar():
        # Leemos el limite escrito en el cuadro.
        try:
            limite = int(creditos.get())
        except ValueError:
            messagebox.showerror(
                "Dato invalido",
                "El limite de creditos debe ser un numero entero."
            )
            return

        if limite < 1 or limite > 60:
            messagebox.showerror(
                "Dato invalido",
                "El limite de creditos debe estar entre 1 y 60."
            )
            return

        if not hay_biblioteca():
            messagebox.showerror(
                "Sin datos",
                "No se cargaron las materias desde el programa en C."
            )
            return

        for fila in tabla.get_children():
            tabla.delete(fila)

        aprobadas = construir_aprobadas()
        pendientes = len(materias) - sum(aprobadas)

        resumen.config(
            text=(
                f"Materias pendientes: {pendientes} | "
                f"Limite: {limite} creditos por semestre"
            )
        )

        # Heuristica voraz con sus dos criterios.
        criterios_voraz = [
            ("Voraz: materias que mas desbloquean", 0),
            ("Voraz: solo por creditos", 1),
        ]

        for texto, criterio in criterios_voraz:
            semestres, asignacion = plan_voraz_c(criterio, limite)

            if semestres < 0:
                messagebox.showerror(
                    "Error",
                    "No se pudo calcular el plan: la malla tiene un "
                    "ciclo de prerrequisitos."
                )
                return

            carga = max(creditos_por_semestre(asignacion).values(), default=0)

            tabla.insert(
                "",
                "end",
                values=(
                    texto,
                    semestres,
                    carga,
                    "Heuristica: no garantiza el minimo"
                )
            )

        # El backtracking puede tardar, asi que se calcula en otro hilo
        # para que la ventana siga respondiendo.
        fila_bt = tabla.insert(
            "",
            "end",
            values=(
                "Backtracking (busqueda exhaustiva)",
                "...",
                "...",
                "Calculando..."
            )
        )
        boton.config(state="disabled")

        respuesta = {}

        def trabajo():
            try:
                respuesta["bt"] = plan_backtracking_c(limite, aprobadas)
            except Exception:
                respuesta["bt"] = {"codigo": -1}

        threading.Thread(target=trabajo, daemon=True).start()

        def revisar():
            try:
                if not tabla.winfo_exists():
                    return
            except tk.TclError:
                return

            if "bt" not in respuesta:
                ventana.after(150, revisar)
                return

            resultado = respuesta["bt"]
            codigo = resultado["codigo"]

            if codigo == 0:
                carga = max(
                    creditos_por_semestre(resultado["asignacion"]).values(),
                    default=0
                )

                if resultado["optimo"]:
                    nota = "Exacto: minimo de semestres demostrado"
                else:
                    nota = (
                        "Plan valido; minimo no demostrado "
                        "(se llego al limite de pasos)"
                    )

                valores = (
                    "Backtracking (busqueda exhaustiva)",
                    resultado["semestres"],
                    carga,
                    nota
                )
            elif codigo == 1:
                valores = (
                    "Backtracking (busqueda exhaustiva)",
                    "-",
                    "-",
                    "Sin plan dentro del limite de pasos"
                )
            elif codigo == -2:
                valores = (
                    "Backtracking (busqueda exhaustiva)",
                    "-",
                    "-",
                    "Hay mas de 64 materias pendientes"
                )
            else:
                valores = (
                    "Backtracking (busqueda exhaustiva)",
                    "-",
                    "-",
                    "Error: ciclo de prerrequisitos o memoria"
                )

            tabla.item(fila_bt, values=valores)
            boton.config(state="normal")

        ventana.after(150, revisar)

    boton = tk.Button(
        panel,
        text="Preparar comparacion",
        command=comparar,
        bg=AZUL,
        fg=BLANCO,
        relief="flat",
        cursor="hand2",
        padx=12,
        pady=8
    )
    boton.pack(side="left", padx=10)


# PLANEACION SEMESTRAL

def mostrar_planeacion():
    limpiar_contenido()

    crear_titulo(
        "Planeacion semestral",
        "Plan sugerido de materias por periodo."
    )

    # El plan lo calcula el programa en C (quicksort + restricciones).
    semestres, asignacion = plan_sugerido_c(
        MAX_CREDITOS_SEMESTRE,
        MAX_DIFICULTAD_SEMESTRE
    )

    if semestres < 0:
        messagebox.showerror(
            "Error",
            "No se pudo calcular el plan. Revisa que las materias se "
            "hayan cargado y que la malla no tenga ciclos."
        )
        return

    filas = []

    for periodo in range(1, semestres + 1):
        for indice, materia in enumerate(materias):
            if asignacion[indice] != periodo:
                continue

            original = f"Semestre {materia[2]}"

            if materia[2] != periodo:
                original += " (movida)"

            filas.append((
                f"Semestre {periodo}",
                materia[0],
                materia[1],
                original
            ))

    crear_tabla(
        ("Periodo", "Materia", "Creditos", "Plan original"),
        filas
    )

    tk.Label(
        contenido,
        text=(
            "Plan calculado con quicksort y las restricciones de "
            f"prerrequisitos (maximo {MAX_CREDITOS_SEMESTRE} creditos y "
            f"dificultad {MAX_DIFICULTAD_SEMESTRE} por semestre). "
            "Las materias movidas cambiaron de semestre respecto al plan "
            "original."
        ),
        bg=FONDO,
        fg="#92400E",
        font=("Segoe UI", 10),
        wraplength=750
    ).pack(anchor="w", padx=30, pady=(0, 15))


# REPORTES

def mostrar_reportes():
    limpiar_contenido()

    crear_titulo(
        "Reportes",
        "Validacion de la malla y creditos por semestre."
    )

    # La validacion se hace en C (recorrido DFS de los prerrequisitos).
    invalidos, ciclos = validar_malla_c()

    panel = tk.Frame(contenido, bg=BLANCO)
    panel.pack(fill="x", padx=30, pady=10)

    tk.Label(
        panel,
        text="Validacion de la malla",
        bg=BLANCO,
        fg=TEXTO,
        font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=20, pady=(20, 8))

    if not hay_biblioteca():
        mensaje = "No se cargaron las materias desde el programa en C."
        color = "#B91C1C"
    elif invalidos == 0 and not ciclos:
        mensaje = "Sin ciclos de prerrequisitos ni indices invalidos."
        color = VERDE
    else:
        lineas = []

        if invalidos > 0:
            lineas.append(
                f"Prerrequisitos con indice invalido: {invalidos}."
            )

        for ciclo in ciclos:
            nombres = [materias[i][0] for i in ciclo]
            nombres.append(nombres[0])
            lineas.append("Ciclo: " + " -> ".join(nombres))

        if ciclos:
            lineas.append('(cada flecha se lee "requiere a")')

        mensaje = "\n".join(lineas)
        color = "#B91C1C"

    tk.Label(
        panel,
        text=mensaje,
        bg=BLANCO,
        fg=color,
        font=("Segoe UI", 10),
        wraplength=750,
        justify="left"
    ).pack(anchor="w", padx=20, pady=(0, 20))

    # Resumen del plan original por semestre.
    filas = []
    total_materias = 0
    total_creditos = 0
    total_dificultad = 0
    total_aprobados = 0

    for semestre in sorted({materia[2] for materia in materias}):
        del_semestre = [m for m in materias if m[2] == semestre]
        creditos = sum(m[1] for m in del_semestre)
        dificultad = sum(m[3] for m in del_semestre)
        aprobados = sum(
            m[1] for m in del_semestre if m[0] in materias_aprobadas
        )

        filas.append((
            f"Semestre {semestre}",
            len(del_semestre),
            creditos,
            dificultad,
            aprobados
        ))

        total_materias += len(del_semestre)
        total_creditos += creditos
        total_dificultad += dificultad
        total_aprobados += aprobados

    filas.append((
        "Total",
        total_materias,
        total_creditos,
        total_dificultad,
        total_aprobados
    ))

    crear_tabla(
        (
            "Periodo",
            "Materias",
            "Creditos",
            "Dificultad total",
            "Creditos aprobados"
        ),
        filas
    )


# MENU LATERAL

tk.Label(
    menu_lateral,
    text="Proyecto",
    font=("Segoe UI", 23, "bold"),
    bg=AZUL_OSCURO,
    fg=BLANCO
).pack(anchor="w", padx=22, pady=(28, 3))

tk.Label(
    menu_lateral,
    text="PLANEACION CURRICULAR",
    font=("Segoe UI", 8, "bold"),
    bg=AZUL_OSCURO,
    fg="#93C5FD"
).pack(anchor="w", padx=22, pady=(0, 25))


def crear_boton_menu(texto, funcion):
    tk.Button(
        menu_lateral,
        text=texto,
        command=funcion,
        font=("Segoe UI", 10),
        bg=AZUL_OSCURO,
        fg=BLANCO,
        activebackground="#1E40AF",
        activeforeground=BLANCO,
        relief="flat",
        cursor="hand2",
        anchor="w",
        padx=22,
        pady=13
    ).pack(fill="x", padx=8, pady=2)


crear_boton_menu("Inicio", mostrar_inicio)
crear_boton_menu("Malla curricular", mostrar_malla)
crear_boton_menu("Materias elegibles", mostrar_elegibles)
crear_boton_menu("Carga academica", mostrar_carga)
crear_boton_menu("Planeacion", mostrar_planeacion)
crear_boton_menu("Reportes", mostrar_reportes)

tk.Label(
    menu_lateral,
    text="Version de desarrollo",
    font=("Segoe UI", 8),
    bg=AZUL_OSCURO,
    fg="#CBD5E1"
).pack(side="bottom", pady=18)

# Si C no pudo cargar la malla, avisamos al usuario
if error_carga is not None:
    messagebox.showerror(
        "No se pudo cargar la malla",
        "El programa en C no pudo leer las materias.\n\n"
        + error_carga
        + "\n\nCompila la biblioteca con compilar_dll.bat "
        "(carpeta gui) y vuelve a abrir el programa."
    )

# Mostrar la primera pantalla
mostrar_inicio()

# Mantener abierta la ventana
ventana.mainloop()
