from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from helynota.database import utcnow


@dataclass
class IndicadorSalida:
    nombre: str
    cumplido: bool
    detalle: str


class MetricasTesting:
    """Calcula indicadores clave para el proceso de pruebas."""

    def __init__(
        self,
        defectos: pd.DataFrame,
        testers_disponibles: int = 5,
        casos_planificados_totales: int = 220,
        casos_automatizados_totales: int = 150,
    ) -> None:
        self.catalogo_defectos = defectos.copy()
        self.testers_disponibles = testers_disponibles
        self.casos_planificados_totales = casos_planificados_totales
        self.casos_automatizados_totales = casos_automatizados_totales

        self.defectos_observados = pd.DataFrame(columns=defectos.columns)
        self.registros_ejecucion = pd.DataFrame(
            columns=[
                "dia",
                "casos_planificados",
                "casos_ejecutados",
                "casos_aprobados",
                "casos_fallidos",
                "casos_automatizados",
            ]
        )
        self.snapshots: List[Dict[str, float]] = []

        self.requisitos = self._crear_catalogo_requisitos()
        self._ultima_actualizacion: Optional[str] = None

    def _crear_catalogo_requisitos(self) -> pd.DataFrame:
        data = [
            ("REQ-001", "Busqueda por fechas", "Alta", 12),
            ("REQ-002", "Filtrado por tipo de habitacion", "Alta", 10),
            ("REQ-003", "Reserva consolidada", "Critica", 18),
            ("REQ-004", "Simulador de pago", "Critica", 15),
            ("REQ-005", "Notificaciones email", "Media", 8),
            ("REQ-006", "Historial de reservas", "Media", 9),
            ("REQ-007", "Autenticacion y sesiones", "Critica", 14),
            ("REQ-008", "Dashboard administrativo", "Media", 7),
            ("REQ-009", "Politicas de cancelacion", "Baja", 6),
            ("REQ-010", "Reporte ocupacion", "Alta", 11),
        ]
        df = pd.DataFrame(
            data,
            columns=["requisito_id", "descripcion", "prioridad", "casos_totales"],
        )
        df["casos_aprobados"] = 0
        return df

    def registrar_dia(
        self,
        fecha: str,
        defectos_dia: pd.DataFrame,
        casos_planificados: int,
        casos_ejecutados: int,
        casos_aprobados: int,
        casos_fallidos: int,
        casos_automatizados: int,
    ) -> Dict[str, float]:
        """Registra los resultados de un día de pruebas y calcula métricas."""
        self._ultima_actualizacion = fecha
        if not defectos_dia.empty:
            self.defectos_observados = pd.concat(
                [self.defectos_observados, defectos_dia], ignore_index=True
            )

        self._actualizar_cobertura(casos_aprobados)

        self.registros_ejecucion = pd.concat(
            [
                self.registros_ejecucion,
                pd.DataFrame(
                    [
                        {
                            "dia": fecha,
                            "casos_planificados": casos_planificados,
                            "casos_ejecutados": casos_ejecutados,
                            "casos_aprobados": casos_aprobados,
                            "casos_fallidos": casos_fallidos,
                            "casos_automatizados": casos_automatizados,
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )

        snapshot = {
            "dia": fecha,
            "defectos_abiertos": self.indicador_defectos_abiertos(),
            "defectos_criticos": self.indicador_defectos_criticos(),
            "tasa_resolucion": self.indicador_tasa_resolucion(),
            "densidad_defectos": self.indicador_densidad_defectos(),
            "tasa_escape": self.indicador_tasa_escape(),
            "productividad": self.indicador_productividad_equipo(casos_ejecutados),
            "tasa_aprobacion": self.indicador_tasa_aprobacion(),
            "automatizacion": self.indicador_automatizacion(),
            "cobertura_requisitos": self.calcular_cobertura()["porcentaje_requisitos"],
        }

        snapshot["criterios_salida_ok"] = self.criterios_salida()
        self.snapshots.append(snapshot)
        return snapshot

    def _actualizar_cobertura(self, casos_aprobados: int) -> None:
        if casos_aprobados <= 0:
            return

        pendientes = self.requisitos[
            self.requisitos["casos_aprobados"] < self.requisitos["casos_totales"]
        ].copy()

        if pendientes.empty:
            return

        restante = casos_aprobados
        for idx in pendientes.index:
            if restante <= 0:
                break
            totales = int(self.requisitos.at[idx, "casos_totales"])
            aprobados = int(self.requisitos.at[idx, "casos_aprobados"])
            espacio = totales - aprobados
            incremento = min(espacio, max(1, restante // len(pendientes)))
            self.requisitos.at[idx, "casos_aprobados"] = aprobados + incremento
            restante -= incremento

    # ===================== Indicadores base ===========================
    def indicador_defectos_abiertos(self) -> int:
        if self.defectos_observados.empty:
            return 0
        return int((self.defectos_observados["estado"] != "Resuelto").sum())

    def indicador_defectos_criticos(self) -> int:
        if self.defectos_observados.empty:
            return 0
        mask = (self.defectos_observados["severidad"] == "Critico") & (
            self.defectos_observados["estado"] != "Resuelto"
        )
        return int(mask.sum())

    def indicador_tasa_resolucion(self) -> float:
        if self.defectos_observados.empty:
            return 0.0
        resueltos = (self.defectos_observados["estado"] == "Resuelto").sum()
        return round(resueltos / len(self.defectos_observados), 3)

    def indicador_densidad_defectos(self) -> float:
        if self.defectos_observados.empty:
            return 0.0
        modulos = self.defectos_observados.groupby("modulo").size()
        return round(modulos.mean(), 2)

    def indicador_tasa_escape(self) -> float:
        if self.defectos_observados.empty:
            return 0.0
        escapes = (self.defectos_observados["ambiente"] == "Produccion").sum()
        return round(escapes / len(self.defectos_observados), 3)

    def indicador_productividad_equipo(self, casos_ejecutados: int) -> float:
        if self.testers_disponibles == 0:
            return 0.0
        return round(casos_ejecutados / self.testers_disponibles, 2)

    def indicador_tasa_aprobacion(self) -> float:
        if self.registros_ejecucion.empty:
            return 0.0
        total_ejecutados = self.registros_ejecucion["casos_ejecutados"].sum()
        if total_ejecutados == 0:
            return 0.0
        total_aprobados = self.registros_ejecucion["casos_aprobados"].sum()
        return round(total_aprobados / total_ejecutados, 3)

    def indicador_automatizacion(self) -> float:
        if self.casos_planificados_totales == 0:
            return 0.0
        automatizados = self.registros_ejecucion["casos_automatizados"].sum()
        return round(automatizados / self.casos_planificados_totales, 3)

    def indicador_tiempo_promedio_resolucion(self) -> float:
        if self.defectos_observados.empty:
            return 0.0
        resueltos = self.defectos_observados[
            self.defectos_observados["estado"] == "Resuelto"
        ]
        if resueltos.empty:
            return 0.0
        return round(resueltos["dias_abierto"].astype(int).mean(), 2)

    # ===================== Funciones solicitadas =======================
    def calcular_cobertura(self) -> Dict[str, float]:
        total_casos = self.requisitos["casos_totales"].sum()
        total_aprobados = self.requisitos["casos_aprobados"].sum()
        requisitos_cubiertos = (
            self.requisitos["casos_aprobados"] >= self.requisitos["casos_totales"]
        ).sum()

        return {
            "porcentaje_casos": round(total_aprobados / total_casos, 3)
            if total_casos
            else 0.0,
            "porcentaje_requisitos": round(
                requisitos_cubiertos / len(self.requisitos), 3
            ),
            "porcentaje_automatizacion": round(
                self.indicador_automatizacion(), 3
            ),
        }

    def detectar_tendencia(self, metrico: str, ventana: int = 3) -> Dict[str, float]:
        if not self.snapshots:
            return {"metrico": metrico, "tendencia": "sin_datos", "delta": 0.0}

        valores = [snap.get(metrico, 0.0) for snap in self.snapshots[-ventana:]]
        if len(valores) < 2:
            return {"metrico": metrico, "tendencia": "estable", "delta": 0.0}

        delta = round(valores[-1] - valores[0], 3)
        if delta > 0.01:
            tendencia = "al_alza"
        elif delta < -0.01:
            tendencia = "a_la_baja"
        else:
            tendencia = "estable"

        return {"metrico": metrico, "tendencia": tendencia, "delta": delta}

    def criterios_salida(self) -> Dict[str, IndicadorSalida]:
        if not self.snapshots:
            return {}
        ultimo = self.snapshots[-1]
        cobertura = self.calcular_cobertura()
        indicadores = {
            "criticos_cerrados": IndicadorSalida(
                "Criticos cerrados",
                ultimo["defectos_criticos"] == 0,
                f"{ultimo['defectos_criticos']} criticos abiertos",
            ),
            "defectos_totales": IndicadorSalida(
                "Defectos abiertos <= 5",
                ultimo["defectos_abiertos"] <= 5,
                f"{ultimo['defectos_abiertos']} abiertos",
            ),
            "tasa_aprobacion": IndicadorSalida(
                "Tasa aprobacion >= 92%",
                ultimo["tasa_aprobacion"] >= 0.92,
                f"{ultimo['tasa_aprobacion']:.0%}",
            ),
            "cobertura_requisitos": IndicadorSalida(
                "Cobertura requisitos >= 85%",
                cobertura["porcentaje_requisitos"] >= 0.85,
                f"{cobertura['porcentaje_requisitos']:.0%}",
            ),
            "automatizacion": IndicadorSalida(
                "Automatizacion >= 60%",
                cobertura["porcentaje_automatizacion"] >= 0.6,
                f"{cobertura['porcentaje_automatizacion']:.0%}",
            ),
            "tasa_escape": IndicadorSalida(
                "Fuga <= 2%",
                ultimo["tasa_escape"] <= 0.02,
                f"{ultimo['tasa_escape']:.1%}",
            ),
            "resolucion": IndicadorSalida(
                "Resolucion >= 80%",
                ultimo["tasa_resolucion"] >= 0.8,
                f"{ultimo['tasa_resolucion']:.0%}",
            ),
            "tiempo_promedio": IndicadorSalida(
                "Tiempo promedio resolucion <= 4 dias",
                self.indicador_tiempo_promedio_resolucion() <= 4,
                f"{self.indicador_tiempo_promedio_resolucion():.1f} dias",
            ),
        }
        return indicadores

    # ======================= Utilidades ================================
    def tendencia_resumen(self) -> Dict[str, Dict[str, float]]:
        metricos = ["defectos_abiertos", "tasa_aprobacion", "automatizacion"]
        return {m: self.detectar_tendencia(m) for m in metricos}

    def exportar_trazabilidad(self, destino: Path) -> None:
        columnas = [
            "requisito_id",
            "descripcion",
            "prioridad",
            "casos_totales",
            "casos_aprobados",
        ]
        df = self.requisitos[columnas].copy()
        df["cobertura"] = (
            df["casos_aprobados"] / df["casos_totales"]
        ).round(3)
        df.to_excel(destino, index=False)

    def resumen_actual(self) -> Dict[str, float]:
        if not self.snapshots:
            return {}
        resumen = self.snapshots[-1].copy()
        resumen["ultima_actualizacion"] = self._ultima_actualizacion or ""
        resumen["timestamp_generado"] = utcnow().isoformat()
        return resumen
