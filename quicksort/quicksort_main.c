// Programa de prueba del modulo de ordenamiento (U2).
// Se compila junto con quicksort.c; quedo separado para que voraz y u4
// puedan usar quicksort.c sin chocar con otro main().
#include "quicksort.h"

int main(int argc, char *argv[]) {
    const char *ruta_archivo = (argc > 1) ? argv[1] : "cursos.txt";

    int n = 0;
    Curso *cursos = leer_cursos_archivo(ruta_archivo, &n);

    if (cursos == NULL || n == 0) {
        printf("No se pudieron leer cursos desde '%s'.\n", ruta_archivo);
        printf("Verifica que el archivo exista y este en el mismo directorio, ");
        printf("o pasa la ruta como argumento: %s <ruta_al_archivo>\n",
               (argc > 0) ? argv[0] : "programa");
        return 1;
    }

    printf("Se leyeron %d cursos desde '%s'\n", n, ruta_archivo);

    // Mostrar datos originales tal como se leyeron del archivo
    imprimir_cursos(cursos, n, "Lista Original (leida desde archivo)", cursos);

    // Prueba Quicksort por dificultad
    Curso *copia_qs = copiar_arreglo_cursos(cursos, n);
    quicksort(copia_qs, n, comparar_dificultad);
    imprimir_cursos(copia_qs, n, "Ordenado con Quicksort (por Dificultad)", cursos);
    liberar_arreglo_cursos(copia_qs, n);

    // Prueba Quicksort por semestre
    Curso *copia_ms = copiar_arreglo_cursos(cursos, n);
    quicksort(copia_ms, n, comparar_semestre);
    imprimir_cursos(copia_ms, n, "Ordenado con Quicksort (por Semestre)", cursos);
    liberar_arreglo_cursos(copia_ms, n);

    // Prueba Quicksort por créditos
    Curso *copia_qs_cred = copiar_arreglo_cursos(cursos, n);
    quicksort(copia_qs_cred, n, comparar_creditos);
    imprimir_cursos(copia_qs_cred, n, "Ordenado con Quicksort (por Créditos)", cursos);
    liberar_arreglo_cursos(copia_qs_cred, n);

    // Prueba Quicksort por nombre
    Curso *copia_qs_nombre = copiar_arreglo_cursos(cursos, n);
    quicksort(copia_qs_nombre, n, comparar_nombre);
    imprimir_cursos(copia_qs_nombre, n, "Ordenado con Quicksort (por Nombre)", cursos);
    liberar_arreglo_cursos(copia_qs_nombre, n);

    // Liberar memoria original
    liberar_arreglo_cursos(cursos, n);

    return 0;
}
