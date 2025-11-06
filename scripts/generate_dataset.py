from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "dataset_defectos.csv"


def main(records: int = 500) -> None:
    fake = Faker("es_MX")
    Faker.seed(1234)
    random.seed(1234)

    modules = [
        "Busqueda",
        "Reservas",
        "Pagos",
        "Autenticacion",
        "Notificaciones",
        "Reportes",
    ]
    severities = ["Critico", "Alto", "Medio", "Bajo"]
    states = ["Abierto", "En progreso", "Resuelto"]
    defect_types = ["Funcional", "UI", "Performance", "Seguridad", "Datos"]
    priorities = ["P1", "P2", "P3", "P4"]
    environments = ["QA", "Staging", "Produccion"]

    start_date = date.today() - timedelta(days=60)

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with DATA_PATH.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "defecto_id",
                "fecha",
                "modulo",
                "severidad",
                "tipo",
                "estado",
                "reportado_por",
                "dias_abierto",
                "prioridad",
                "ambiente",
                "ciclo",
                "version",
            ],
        )
        writer.writeheader()

        for defect_id in range(1, records + 1):
            days_offset = random.randint(0, 59)
            discovered = start_date + timedelta(days=days_offset)
            estado = random.choices(states, weights=[0.2, 0.3, 0.5], k=1)[0]
            dias_abierto = 0 if estado == "Resuelto" else random.randint(1, 10)
            writer.writerow(
                {
                    "defecto_id": f"D{defect_id:04d}",
                    "fecha": discovered.isoformat(),
                    "modulo": random.choice(modules),
                    "severidad": random.choices(severities, weights=[0.1, 0.3, 0.4, 0.2], k=1)[
                        0
                    ],
                    "tipo": random.choice(defect_types),
                    "estado": estado,
                    "reportado_por": fake.name(),
                    "dias_abierto": dias_abierto,
                    "prioridad": random.choice(priorities),
                    "ambiente": random.choice(environments),
                    "ciclo": f"Sprint {random.randint(1, 12)}",
                    "version": f"v{random.randint(1, 3)}.{random.randint(0, 9)}",
                }
            )

    print(f"Dataset guardado en {DATA_PATH}")


if __name__ == "__main__":
    main()
