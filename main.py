# main.py

import json
import click
from optimizador.models import PiezaInventario, PiezaModelo, ModeloMueble
from optimizador.logic import optimizar_uso_inventario

def load_data(path, cls):
    with open(path, 'r', encoding='utf-8') as f:
        items = json.load(f)
    return [cls(**i) for i in items]

@click.command()
@click.option('--modelo-id', required=True, type=int, help="ID del modelo de mueble")
@click.option('--cantidad', required=True, type=int, help="Cantidad deseada")
def cli(modelo_id, cantidad):
    inv = load_data('data/inventario.json', PiezaInventario)
    modelos = load_data('data/modelos.json', ModeloMueble)
    modelo = next((m for m in modelos if m.id == modelo_id), None)
    if not modelo:
        click.echo(f"⚠️  Modelo con id={modelo_id} no encontrado.")
        return
    resultado = optimizar_uso_inventario(modelo, inv, cantidad)
    click.echo(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    cli()
