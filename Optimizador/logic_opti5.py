# optimizador/logic_opti5.py

import random
import math
from copy import deepcopy
from typing import List, Dict
from optimizador.models import PiezaInventario, ModeloMueble, PiezaModelo

# Representa una solución
class Estado:
    def __init__(self, piezas: List[PiezaModelo], tableros: List[PiezaInventario]):
        self.asignacion = {i: [] for i in range(len(tableros))}  # índice tablero -> piezas
        self.tableros = deepcopy(tableros)
        self.piezas = deepcopy(piezas)
        self._inicializar_asignacion()

    def _inicializar_asignacion(self):
        todas = []
        for p in self.piezas:
            todas.extend([p] * p.cantidad)
        random.shuffle(todas)

        for pieza in todas:
            for i, tablero in enumerate(self.tableros):
                if self._cabe(pieza, tablero):
                    self.asignacion[i].append(pieza)
                    break

    def _cabe(self, pieza: PiezaModelo, tablero: PiezaInventario):
        return (
            (pieza.ancho <= tablero.ancho and pieza.largo <= tablero.largo)
            or (pieza.largo <= tablero.ancho and pieza.ancho <= tablero.largo)
        )

    def energia(self):
        uso = 0
        desperdicio_total = 0
        for i, piezas in self.asignacion.items():
            if piezas:
                uso += 1
                area_piezas = sum(p.ancho * p.largo for p in piezas)
                area_tablero = self.tableros[i].ancho * self.tableros[i].largo
                desperdicio_total += (area_tablero - area_piezas)
        return uso * 100000 + desperdicio_total  # Penalizar fuerte el uso excesivo de tableros

    def mutar(self):
        i_origen = random.choice(list(self.asignacion.keys()))
        if not self.asignacion[i_origen]:
            return
        pieza = random.choice(self.asignacion[i_origen])
        self.asignacion[i_origen].remove(pieza)

        destinos = list(self.asignacion.keys())
        random.shuffle(destinos)

        for i_dest in destinos:
            if self._cabe(pieza, self.tableros[i_dest]):
                self.asignacion[i_dest].append(pieza)
                return
        # si no cupo, vuelve al origen
        self.asignacion[i_origen].append(pieza)

    def clonar(self):
        nuevo = Estado(self.piezas, self.tableros)
        nuevo.asignacion = deepcopy(self.asignacion)
        return nuevo


def simulated_annealing_optimize(
    modelo: ModeloMueble,
    inventario: List[PiezaInventario],
    cantidad_deseada: int,
    max_iter: int = 1000,
    temp_inicial: float = 1000.0,
    enfriamiento: float = 0.95,
    debug: bool = True
) -> List[Dict]:

    piezas_total = []
    for pieza in modelo.piezas:
        piezas_total.extend([pieza] * cantidad_deseada)

    estado_actual = Estado(piezas_total, inventario)
    mejor_estado = estado_actual.clonar()
    temp = temp_inicial

    for iteracion in range(max_iter):
        nuevo_estado = estado_actual.clonar()
        nuevo_estado.mutar()

        delta_e = nuevo_estado.energia() - estado_actual.energia()
        if delta_e < 0 or random.random() < math.exp(-delta_e / temp):
            estado_actual = nuevo_estado
            if estado_actual.energia() < mejor_estado.energia():
                mejor_estado = estado_actual.clonar()

        temp *= enfriamiento
        if debug and iteracion % 100 == 0:
            print(f"Iteración {iteracion}, Energía: {estado_actual.energia():.2f}, Mejor: {mejor_estado.energia():.2f}")

    # Armar resultado por tablero
    resultados = []
    for i, piezas in mejor_estado.asignacion.items():
        if piezas:
            tablero = inventario[i]
            piezas_formato = []
            contador = {}
            for p in piezas:
                key = p.codigo
                contador[key] = contador.get(key, 0) + 1
            for cod, qty in contador.items():
                piezas_formato.append({
                    "codigo": tablero.codigo,
                    "color": tablero.color,
                    "largo": tablero.largo,
                    "ancho": tablero.ancho,
                    "espesor": tablero.espesor,
                    "pieza_modelo_codigo": cod,
                    "cantidad_req": qty
                })
            resultados.append(piezas_formato)

    return [{
        "color":              "Global",
        "cantidadSolicitada": cantidad_deseada,
        "cantidadFabricable": cantidad_deseada,
        "piezasUtilizadas":   resultados
    }]
