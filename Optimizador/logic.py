# optimizador/logic_nivel2.py

from copy import deepcopy
from math import floor, ceil
from typing import List, Dict
from optimizador.models import PiezaInventario, ModeloMueble, PiezaModelo

def optimizar_por_color(
    modelo: ModeloMueble,
    inventario: List[PiezaInventario],
    cantidad_deseada: int
) -> List[Dict]:
    """
    Optimiza piezas eliminando márgenes y permitiendo múltiples cortes por sobrante.
    """
    resultados = []
    colores = sorted({p.color for p in inventario})

    for color in colores:
        inv_color = [deepcopy(p) for p in inventario if p.color == color]
        inv_color.sort(key=lambda p: (p.espesor, p.largo * p.ancho))

        fabricables = 0
        piezas_usadas = []

        for _ in range(cantidad_deseada):
            lote = []
            for req in modelo.piezas:
                candidatos = []

                for p in inv_color:
                    if req.espesor > 0 and p.espesor != req.espesor:
                        continue

                    # Permitir rotación y validar tamaño
                    fits_normal = p.ancho >= req.ancho and p.largo >= req.largo
                    fits_rotated = p.ancho >= req.largo and p.largo >= req.ancho

                    if not (fits_normal or fits_rotated):
                        continue

                    # Calcular máximo de piezas que caben
                    f1 = floor(p.largo / req.largo) * floor(p.ancho / req.ancho)
                    f2 = floor(p.largo / req.ancho) * floor(p.ancho / req.largo)
                    fit_count = max(f1, f2)

                    if fit_count == 0:
                        continue

                    tablas_req = ceil(req.cantidad / fit_count)

                    if p.cantidad < tablas_req:
                        continue

                    used_area = req.largo * req.ancho * fit_count
                    tablero_area = p.largo * p.ancho
                    waste = tablero_area - used_area

                    candidatos.append((p, fit_count, tablas_req, waste))

                if not candidatos:
                    lote = None
                    break

                # Elegir el candidato con menor desperdicio
                p_sel, fit_count, tablas_req, _ = min(
                    candidatos,
                    key=lambda tpl: tpl[3]
                )

                p_sel.cantidad -= tablas_req

                lote.append({
                    "codigo":          p_sel.codigo,
                    "color":           p_sel.color,
                    "largo":           p_sel.largo,
                    "ancho":           p_sel.ancho,
                    "espesor":         p_sel.espesor,
                    "cantidad_req":    req.cantidad,
                    "fit_count":       fit_count,
                    "tableros_usados": tablas_req
                })

            if lote is None:
                break

            fabricables += 1
            piezas_usadas.append(lote)

        resultados.append({
            "color":              color or "Sin color",
            "cantidadSolicitada": cantidad_deseada,
            "cantidadFabricable": fabricables,
            "piezasUtilizadas":   piezas_usadas
        })

    return resultados
