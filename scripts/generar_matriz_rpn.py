from __future__ import annotations

import random
from pathlib import Path

import pandas as pd


def generar_matriz(destino: Path) -> None:
    funcionalidades = [
        "Busqueda por fechas",
        "Filtro por tipo",
        "Disponibilidad en tiempo real",
        "Proceso de reserva",
        "Simulacion de pago",
        "Validacion de tarjetas",
        "Notificacion por correo",
        "Gestion de perfiles",
        "Cancelacion flexible",
        "Reporte ocupacion",
    ]

    random.seed(42)
    registros = []
    for funcionalidad in funcionalidades:
        severidad = random.randint(3, 10)
        ocurrencia = random.randint(2, 9)
        deteccion = random.randint(2, 8)
        rpn = severidad * ocurrencia * deteccion
        if rpn >= 300:
            riesgo = "Critico"
        elif rpn >= 200:
            riesgo = "Alto"
        elif rpn >= 120:
            riesgo = "Medio"
        else:
            riesgo = "Bajo"
        registros.append(
            {
                "Funcionalidad": funcionalidad,
                "Severidad": severidad,
                "Ocurrencia": ocurrencia,
                "Deteccion": deteccion,
                "RPN": rpn,
                "Nivel_Riesgo": riesgo,
                "Accion_Mitigacion": sugerir_accion(riesgo),
            }
        )

    df = pd.DataFrame(registros)
    destino.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(destino, index=False)


def sugerir_accion(riesgo: str) -> str:
    acciones = {
        "Critico": "Plan de mitigacion inmediato y prueba diaria",
        "Alto": "Incrementar cobertura automatizada y validar escenarios limite",
        "Medio": "Revisar casos de prueba y reforzar pruebas exploratorias",
        "Bajo": "Monitoreo continuo, sin acciones adicionales",
    }
    return acciones[riesgo]


if __name__ == "__main__":
    destino = Path(__file__).resolve().parents[1] / "Matriz_Riesgo_RPN.xlsx"
    generar_matriz(destino)
    print(f"Matriz de riesgo generada en {destino}")
