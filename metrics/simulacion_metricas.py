from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import pandas as pd

from metrics.sistema_metricas import MetricasTesting


BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = BASE_DIR / "data" / "dataset_defectos.csv"
DASHBOARD_DIR = BASE_DIR / "dashboards"


def _fig_to_base64(fig: plt.Figure) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode("utf-8")


def _build_dashboard_html(
    snapshot: Dict[str, float],
    historico: pd.DataFrame,
    criterios: Dict[str, object],
    ruta_salida: Path,
) -> None:
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    fig1, ax1 = plt.subplots(figsize=(6, 3))
    ax1.plot(historico["dia"], historico["defectos_abiertos"], marker="o", color="#d9534f")
    ax1.set_title("Defectos abiertos por día")
    ax1.set_ylabel("Defectos")
    ax1.set_xlabel("Día")
    ax1.grid(True, linestyle="--", alpha=0.4)
    grafico_defectos = _fig_to_base64(fig1)

    fig2, ax2 = plt.subplots(figsize=(6, 3))
    ax2.plot(historico["dia"], historico["tasa_aprobacion"], marker="o", color="#5cb85c")
    ax2.set_title("Tasa de aprobación acumulada")
    ax2.set_ylabel("Porcentaje")
    ax2.set_xlabel("Día")
    ax2.set_ylim(0, 1)
    ax2.grid(True, linestyle="--", alpha=0.4)
    grafico_aprobacion = _fig_to_base64(fig2)

    criterios_rows = "\n".join(
        f"<tr><td>{c.nombre}</td>"
        f"<td style='color:{'green' if c.cumplido else 'red'};'>{'OK' if c.cumplido else 'Pendiente'}</td>"
        f"<td>{c.detalle}</td></tr>"
        for c in criterios.values()
    )

    resumen_rows = "\n".join(
        f"<tr><th>{clave.replace('_', ' ').title()}</th><td>{valor}</td></tr>"
        for clave, valor in snapshot.items()
        if clave not in {"criterios_salida_ok", "dia"}
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8" />
    <title>Dashboard día {snapshot['dia']}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 30px; }}
        h1 {{ color: #1b3c59; }}
        section {{ margin-bottom: 30px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #e1e1e1; padding: 8px; text-align: left; }}
        th {{ background-color: #f5f5f5; }}
        .grafico {{ display: inline-block; margin-right: 10px; }}
    </style>
</head>
<body>
    <h1>Dashboard de Métricas - Día {snapshot['dia']}</h1>
    <section>
        <h2>Resumen Ejecutivo</h2>
        <table>{resumen_rows}</table>
    </section>
    <section>
        <h2>Evolución de métricas</h2>
        <div class="grafico">
            <img src="data:image/png;base64,{grafico_defectos}" alt="Defectos abiertos" />
        </div>
        <div class="grafico">
            <img src="data:image/png;base64,{grafico_aprobacion}" alt="Tasa aprobación" />
        </div>
    </section>
    <section>
        <h2>Criterios de salida</h2>
        <table>
            <tr><th>Indicador</th><th>Estado</th><th>Detalle</th></tr>
            {criterios_rows}
        </table>
    </section>
</body>
</html>
"""

    ruta_salida.write_text(html, encoding="utf-8")


def simular_ejecucion() -> List[Dict[str, float]]:
    defectos = pd.read_csv(DATASET_PATH)
    defectos["fecha"] = pd.to_datetime(defectos["fecha"]).dt.date

    metricas = MetricasTesting(defectos)

    dias_unicos = sorted(defectos["fecha"].unique())[-5:]
    escenario = [
        {"plan": 40, "exec": 36, "pass": 32, "fail": 4, "auto": 20},
        {"plan": 45, "exec": 42, "pass": 39, "fail": 3, "auto": 25},
        {"plan": 45, "exec": 44, "pass": 41, "fail": 3, "auto": 30},
        {"plan": 50, "exec": 48, "pass": 46, "fail": 2, "auto": 35},
        {"plan": 50, "exec": 49, "pass": 47, "fail": 2, "auto": 40},
    ]

    snapshots: List[Dict[str, float]] = []
    for indice, fecha in enumerate(dias_unicos):
        datos_dia = escenario[min(indice, len(escenario) - 1)]
        defectos_dia = defectos[defectos["fecha"] == fecha]
        snapshot = metricas.registrar_dia(
            fecha.isoformat(),
            defectos_dia,
            datos_dia["plan"],
            datos_dia["exec"],
            datos_dia["pass"],
            datos_dia["fail"],
            datos_dia["auto"],
        )
        snapshots.append(snapshot)
        historico = pd.DataFrame(metricas.snapshots)
        criterios = metricas.criterios_salida()
        salida = DASHBOARD_DIR / f"dashboard_dia_{indice + 1}.html"
        _build_dashboard_html(snapshot, historico, criterios, salida)

    resumen_path = DASHBOARD_DIR / "resumen_metricas.csv"
    pd.DataFrame(snapshots).to_csv(resumen_path, index=False)

    trazabilidad_path = BASE_DIR / "Matriz_Trazabilidad.xlsx"
    metricas.exportar_trazabilidad(trazabilidad_path)

    return snapshots


if __name__ == "__main__":
    resultados = simular_ejecucion()
    print("Simulación completada. Dashboards generados en:", DASHBOARD_DIR)
