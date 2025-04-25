# optimizador/logic.py

from typing import List, Dict
from optimizador.models import PiezaInventario, ModeloMueble

def optimizar_uso_inventario(
    modelo: ModeloMueble,
    inventario: List[PiezaInventario],
    cantidad_deseada: int
) -> Dict:
    # Copia profunda del inventario para simular consumo
    inv = [p for p in inventario]
    resultado = {
        "modelo": modelo.nombre,
        "cantidad_solicitada": cantidad_deseada,
        "cantidad_fabricable": 0,
        "piezas_utilizadas": []  # List of (codigo, descripcion, piezaReq)
    }

    for _ in range(cantidad_deseada):
        piezas_para_este = []
        for pieza_req in modelo.piezas:
            # Buscar en inventario primera pieza válida con stock
            match = next((p for p in inv
                          if p.largo >= pieza_req.largo
                          and p.ancho >= pieza_req.ancho
                          and (pieza_req.espesor is None or p.espesor == pieza_req.espesor)
                          and p.cantidad >= pieza_req.cantidad), None)
            if not match:
                return resultado   # no más muebles posibles
            # “Consumimos” la pieza
            match.cantidad -= pieza_req.cantidad
            piezas_para_este.append({
                "codigo": match.codigo,
                "descripcion": pieza_req.descripcion,
                "largo": pieza_req.largo,
                "ancho": pieza_req.ancho,
                "cantidad": pieza_req.cantidad
            })
        resultado["cantidad_fabricable"] += 1
        resultado["piezas_utilizadas"].append(piezas_para_este)
    return resultado
