#ifndef CRITERIOS_PUENTE_H
#define CRITERIOS_PUENTE_H

/*
 * Declaraciones que quicksort.c (version actual) usa para ordenar por varios
 * criterios, pero que todavia no estan en quicksort.h:
 *   Criterio, CampoCriterio, MAX_CRITERIOS,
 *   configurar_criterios() y comparar_compuesto().
 *
 * El puente de la interfaz las necesita, y quicksort.c se compila con
 *   -include criterios.h
 * para no tener que modificar quicksort.h. Cuando esas declaraciones pasen a
 * quicksort.h, se puede borrar este archivo y quitar el -include de
 * compilar_dll.bat.
 */

typedef enum {
    CRIT_CREDITOS,
    CRIT_DIFICULTAD,
    CRIT_SEMESTRE,
    CRIT_NOMBRE
} CampoCriterio;

typedef struct {
    CampoCriterio campo;
    int descendente;   /* 1 = de mayor a menor */
} Criterio;

#define MAX_CRITERIOS 4

void configurar_criterios(const Criterio *criterios, int n);
int comparar_compuesto(const void *a, const void *b);

#endif /* CRITERIOS_PUENTE_H */
