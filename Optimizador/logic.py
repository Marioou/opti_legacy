# optimizador/logic_nivel2 V5.0 

from copy import deepcopy
from math import floor
from typing import List, Dict
from optimizador.models import PiezaInventario, ModeloMueble, PiezaModelo

def optimizar_por_color(
    modelo: ModeloMueble,
    inventario: List[PiezaInventario],
    cantidad_deseada: int,
    debug: bool = True
) -> List[Dict]:
    """
    Optimización PRO V2 con modo DEBUG.
    """
    resultados = []
    colores = sorted({p.color for p in inventario})

    for color in colores:
        inv_color = [deepcopy(p) for p in inventario if p.color == color]
        inv_color.sort(key=lambda p: (p.espesor, p.largo * p.ancho))

        fabricables = 0
        piezas_usadas = []

        for n_fabricado in range(cantidad_deseada):
            lote = []
            piezas_restantes = deepcopy(modelo.piezas)

            if debug:
                print(f"\n--- Fabricando unidad {n_fabricado+1} ---")

            while piezas_restantes:
                inv_color = [p for p in inv_color if p.cantidad > 0]
                if not inv_color:
                    if debug:
                        print("No hay más sobrantes disponibles.")
                    lote = None
                    break

                sobrante = inv_color.pop(0)
                sobrante_area_total = sobrante.largo * sobrante.ancho
                area_disponible = sobrante_area_total

                if debug:
                    print(f"\nUsando sobrante: {sobrante.codigo} - Área: {sobrante_area_total} mm²")

                tablero_piezas = []
                piezas_colocadas = []
                nuevas_restantes = []

                for req in piezas_restantes:
                    pieza_area = req.ancho * req.largo

                    if pieza_area > area_disponible:
                        nuevas_restantes.append(req)
                        continue

                    fits_normal = sobrante.ancho >= req.ancho and sobrante.largo >= req.largo
                    fits_rotated = sobrante.ancho >= req.largo and sobrante.largo >= req.ancho

                    if not (fits_normal or fits_rotated):
                        nuevas_restantes.append(req)
                        continue

                    piezas_a_colocar = min(req.cantidad, floor(area_disponible / pieza_area))

                    if piezas_a_colocar <= 0:
                        nuevas_restantes.append(req)
                        continue

                    tablero_piezas.append({
                        "codigo": sobrante.codigo,
                        "color": sobrante.color,
                        "largo": sobrante.largo,
                        "ancho": sobrante.ancho,
                        "espesor": sobrante.espesor,
                        "cantidad_req": piezas_a_colocar,
                        "pieza_modelo_codigo": req.codigo,
                    })

                    area_disponible -= piezas_a_colocar * pieza_area

                    if debug:
                        print(f"Colocadas {piezas_a_colocar} piezas del modelo {req.codigo}.")
                        print(f"Área restante en sobrante: {area_disponible} mm².")

                    if req.cantidad > piezas_a_colocar:
                        nuevas_restantes.append(PiezaModelo(
                            codigo=req.codigo,
                            ancho=req.ancho,
                            largo=req.largo,
                            espesor=req.espesor,
                            cantidad=req.cantidad - piezas_a_colocar
                        ))

                if tablero_piezas:
                    lote.extend(tablero_piezas)
                    sobrante.cantidad -= 1
                    piezas_restantes = nuevas_restantes
                    if debug:
                        print(f"Sobrante {sobrante.codigo} agotado o lleno.")
                else:
                    break

            if lote is None:
                break

            fabricables += 1
            piezas_usadas.append(lote)

            if debug:
                print(f"Unidad {n_fabricado+1} fabricada correctamente.\n")

        resultados.append({
            "color":              color or "Sin color",
            "cantidadSolicitada": cantidad_deseada,
            "cantidadFabricable": fabricables,
            "piezasUtilizadas":   piezas_usadas
        })

    return resultados
