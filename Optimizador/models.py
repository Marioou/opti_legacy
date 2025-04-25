# optimizador/models.py

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class PiezaInventario:
    codigo: str
    largo: float
    ancho: float
    espesor: Optional[float]
    cantidad: int

@dataclass
class PiezaModelo:
    descripcion: str
    largo: float
    ancho: float
    espesor: Optional[float]
    cantidad: int

@dataclass
class ModeloMueble:
    id: int
    nombre: str
    piezas: List[PiezaModelo]
