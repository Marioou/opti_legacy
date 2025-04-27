# optimizador/models.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PiezaInventario:
    codigo: str
    ancho: float
    largo: float
    color: str
    espesor: Optional[float]
    cantidad: int

@dataclass
class PiezaModelo:
    codigo: str
    ancho: float
    largo: float
    espesor: Optional[float]
    cantidad: int

@dataclass
class ModeloMueble:
    id: int
    nombre: str
    piezas: List[PiezaModelo]