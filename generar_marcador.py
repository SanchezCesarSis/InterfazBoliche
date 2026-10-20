# -*- coding: utf-8 -*-
"""
Genera un archivo Excel para anotar partidas de Boliche (Bowling).
Reglas implementadas:
 - 10 frames por partida.
 - Strike (10 en el primer lanzamiento): bonificacion = 10 + dos siguientes lanzamientos.
 - Spare (10 en dos lanzamientos): bonificacion = 10 + siguiente lanzamiento.
 - Frame 10: hasta 3 lanzamientos si hay strike o spare.
 - El puntaje total se acumula frame a frame.
Uso posterior: la camara/IA puede escribir los lanzamientos en las celdas de la fila
"Lanzamientos" de cada frame y el Excel calcula solo el puntaje.
"""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.worksheet.datavalidation import DataValidation

N_JUGADORES = 4
FILAS_POR_JUGADOR = 6  # nombre, frames, lanzamientos, puntos(aux), puntaje acumulado, separador

AZUL = "1F4E78"
AZUL_CLARO = "D6EAF8"
GRIS = "F2F3F4"
ORO = "F9E79F"
BLANCO = "FFFFFF"

thin = Side(style="thin", color="999999")
medium = Side(style="medium", color="333333")
BORDE = Border(left=thin, right=thin, top=thin, bottom=thin)
BORDE_GRUESO = Border(left=medium, right=medium, top=medium, bottom=medium)


def col_lanzamiento(frame, lanz):
    """Columna (1-based) de un lanzamiento. Frames 1-9: 2 celdas; frame 10: 3 celdas."""
    if frame < 10:
        return 2 + 2 * (frame - 1) + (lanz - 1)  # B=2 ...
    return 2 + 18 + (lanz - 1)  # T,U,V


def ref(frame, lanz, fila):
    c = get_column_letter(col_lanzamiento(frame, lanz))
    return f"{c}{fila}"


def celdas_planas(frame_ini):
    """Lista plana de celdas de lanzamientos desde frame_ini en adelante (para bonus)."""
    cells = []
    for g in range(frame_ini, 11):
        n = 3 if g == 10 else 2
        for k in range(1, n + 1):
            cells.append((g, k))
    return cells


def expr_siguientes_lanzamientos(frame, n, fila):
    """
    Devuelve (expr_suma, expr_disponible) para los proximos n lanzamientos reales.
    Si un frame 1-9 tiene strike, su 2da celda queda vacia y el siguiente lanzamiento
    real es el primer lanzamiento del frame siguiente.
    """
    cells = celdas_planas(frame + 1)[: n + 1]
    exprs = []
    disp = []
    for i in range(n):
        g, k = cells[i]
        celda = ref(g, k, fila)
        disp.append(f"ISNUMBER({celda})")
        if i == 0:
            exprs.append(celda)
        else:
            g_prev, k_prev = cells[i - 1]
            if g_prev < 10 and k_prev == 1:
                # si el lanzamiento anterior fue strike, salta la 2da celda del frame
                g_skip, k_skip = cells[i + 1]
                exprs.append(
                    f"IF({ref(g_prev, k_prev, fila)}=10,{ref(g_skip, k_skip, fila)},{celda})"
                )
                disp[-1] = (
                    f"IF({ref(g_prev, k_prev, fila)}=10,"
                    f"ISNUMBER({ref(g_skip, k_skip, fila)}),ISNUMBER({celda}))"
                )
            else:
                exprs.append(celda)
    return "+".join(exprs), "AND(" + ",".join(disp) + ")"


def formula_puntos(frame, fila):
    """Puntos del frame (sin acumular) segun reglas de Boliche."""
    r1 = ref(frame, 1, fila)
    r2 = ref(frame, 2, fila)
    if frame == 10:
        r3 = ref(frame, 3, fila)
        return (
            f'IF(OR(NOT(ISNUMBER({r1})),NOT(ISNUMBER({r2}))),"",'
            f'IF({r1}+{r2}<10,{r1}+{r2},'
            f'IF(NOT(ISNUMBER({r3})),"",{r1}+{r2}+{r3})))'
        )
    b1, disp1 = expr_siguientes_lanzamientos(frame, 1, fila)
    b2, disp2 = expr_siguientes_lanzamientos(frame, 2, fila)
    return (
        f'IF(AND(ISNUMBER({r1}),{r1}=10),IF(AND({disp2}),10+{b2},""),'
        f'IF(AND(ISNUMBER({r1}),ISNUMBER({r2}),{r1}+{r2}=10),'
        f'IF({disp1},10+{b1},""),'
        f'IF(AND(ISNUMBER({r1}),ISNUMBER({r2})),{r1}+{r2},"")))'
    )


def formula_acumulado(frame, fila_puntos, fila_acum):
    """Puntaje acumulado hasta este frame (fila de puntos como auxiliar)."""
    c1 = get_column_letter(col_lanzamiento(frame, 1))
    p = f"{c1}{fila_puntos}"
    if frame == 1:
        return f'=IF({p}="","",{p})'
    prev = f"{get_column_letter(col_lanzamiento(frame - 1, 1))}{fila_acum}"
    return f'=IF({p}="","",IF({prev}="","",{prev}+{p}))'


def crear_excel(ruta):
    wb = Workbook()

    # ---------------- Hoja Marcador ----------------
    ws = wb.active
    ws.title = "Marcador"
    ws.sheet_view.showGridLines = False

    ws["B1"] = "MARCADOR DE BOLICHE"
    ws["B1"].font = Font(bold=True, size=16, color=AZUL)
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=22)
    ws["B1"].alignment = Alignment(horizontal="center")

    ws["B2"] = "Fecha:"
    ws["B2"].font = Font(bold=True)
    ws["C2"] = ""
    ws["C2"].number_format = "dd/mm/yyyy"
    ws["E2"] = "Cancha / Local:"
    ws["E2"].font = Font(bold=True)

    # Ancho de columnas
    ws.column_dimensions["A"].width = 2
    for c in range(2, 22):
        ws.column_dimensions[get_column_letter(c)].width = 4.2
    ws.column_dimensions["W"].width = 12
    ws.column_dimensions["B"].width = 14  # nombres a la izquierda? no, nombres arriba

    dv = DataValidation(type="whole", operator="between", formula1=0, formula2=10,
                        allow_blank=True, showErrorMessage=True,
                        errorTitle="Lanzamiento inválido",
                        error="Ingresá un valor entero entre 0 y 10 (pinos derribados).")
    ws.add_data_validation(dv)

    fila_base = 4
    for j in range(N_JUGADORES):
        f_nom = fila_base + j * FILAS_POR_JUGADOR
        f_frames = f_nom + 1
        f_lanz = f_nom + 2
        f_puntos = f_nom + 3
        f_acum = f_nom + 4

        # Nombre del jugador
        ws.cell(f_nom, 2, f"Jugador {j + 1}:").font = Font(bold=True, size=11)
        nombre_cell = ws.cell(f_nom, 3)
        nombre_cell.border = Border(bottom=Side(style="medium", color=AZUL))
        nombre_cell.font = Font(bold=True)
        ws.merge_cells(start_row=f_nom, start_column=3, end_row=f_nom, end_column=8)

        # Frames 1-9: encabezado de 2 columnas; frame 10: 3 columnas
        for fr in range(1, 10):
            c1 = col_lanzamiento(fr, 1)
            c2 = col_lanzamiento(fr, 2)
            ws.merge_cells(start_row=f_frames, start_column=c1, end_row=f_frames, end_column=c2)
            cell = ws.cell(f_frames, c1, fr)
            cell.font = Font(bold=True, color=BLANCO)
            cell.fill = PatternFill("solid", fgColor=AZUL)
            cell.alignment = Alignment(horizontal="center")
        ws.merge_cells(start_row=f_frames, start_column=20, end_row=f_frames, end_column=22)
        cell = ws.cell(f_frames, 20, 10)
        cell.font = Font(bold=True, color=BLANCO)
        cell.fill = PatternFill("solid", fgColor="C0392B")
        cell.alignment = Alignment(horizontal="center")

        # Fila de lanzamientos
        for col in range(2, 23):
            cell = ws.cell(f_lanz, col)
            cell.border = BORDE
            cell.alignment = Alignment(horizontal="center")
            cell.number_format = "0"
            dv.add(cell)

        # Marcar visualmente los 10 (strike o segundo lanzamiento de spare)
        rango_lanz = f"B{f_lanz}:V{f_lanz}"
        ws.conditional_formatting.add(
            rango_lanz,
            CellIsRule(operator="equal", formula=["10"],
                       fill=PatternFill("solid", fgColor=ORO), font=Font(bold=True)),
        )

        # Fila auxiliar de puntos por frame (cada frame en su columna inicial)
        for fr in range(1, 11):
            c1 = col_lanzamiento(fr, 1)
            c_fin = col_lanzamiento(fr, 2) if fr < 10 else 22
            ws.merge_cells(start_row=f_puntos, start_column=c1, end_row=f_puntos, end_column=c_fin)
            cell = ws.cell(f_puntos, c1, "=" + formula_puntos(fr, f_lanz))
            cell.font = Font(size=8, color="999999")
            cell.alignment = Alignment(horizontal="center")

        # Fila de puntaje acumulado por frame
        for fr in range(1, 11):
            c1 = col_lanzamiento(fr, 1)
            c_fin = col_lanzamiento(fr, 2) if fr < 10 else 22
            ws.merge_cells(start_row=f_acum, start_column=c1, end_row=f_acum, end_column=c_fin)
            cell = ws.cell(f_acum, c1, formula_acumulado(fr, f_puntos, f_acum))
            cell.font = Font(bold=True, color=AZUL)
            cell.fill = PatternFill("solid", fgColor=AZUL_CLARO)
            cell.alignment = Alignment(horizontal="center")
            for cc in range(c1, c_fin + 1):
                ws.cell(f_acum, cc).border = BORDE

        # Total general
        ws.cell(f_nom, 23, "TOTAL").font = Font(bold=True, color=BLANCO)
        ws.cell(f_nom, 23).fill = PatternFill("solid", fgColor=AZUL)
        ws.cell(f_nom, 23).alignment = Alignment(horizontal="center")
        # el acumulado del frame 10 esta en la celda izquierda del merge (col 20 = T)
        total = ws.cell(f_acum, 23, f"=T{f_acum}")
        total.font = Font(bold=True, size=12, color=BLANCO)
        total.fill = PatternFill("solid", fgColor="C0392B")
        total.alignment = Alignment(horizontal="center")
        total.border = BORDE_GRUESO

        # Fila auxiliar oculta (calculo intermedio de puntos por frame)
        ws.row_dimensions[f_puntos].hidden = True

    # Leyenda general
    leyenda = fila_base + N_JUGADORES * FILAS_POR_JUGADOR + 1
    ws.cell(leyenda, 2, "Cómo anotar:").font = Font(bold=True, color=AZUL)
    textos = [
        "Solo se cargan datos en la fila 'Lanzamientos' de cada frame. Las filas de puntos y acumulado se calculan solas.",
        "Strike (10 pinos al 1er lanzamiento): escribir 10 en la primera celda del frame y dejar la segunda vacía. Se bonifica +10 + los dos siguientes lanzamientos.",
        "Spare (10 pinos en dos lanzamientos): escribir los pinos de cada lanzamiento (ej. 7 y 3). Se bonifica +10 + el siguiente lanzamiento.",
        "Frame abierto: escribir los pinos de cada lanzamiento (ej. 4 y 5).",
        "Frame 10: si hay strike o spare se usan hasta 3 celdas; si no, solo 2.",
        "El puntaje acumulado (fila azul clara) se muestra cuando el frame y sus bonificaciones están completos. Los valores 10 se resaltan en amarillo.",
    ]
    for i, t in enumerate(textos):
        c = ws.cell(leyenda + 1 + i, 2, t)
        c.font = Font(size=9, color="555555")
        ws.merge_cells(start_row=leyenda + 1 + i, start_column=2, end_row=leyenda + 1 + i, end_column=22)

    ws.freeze_panes = "B4"

    # ---------------- Hoja Instrucciones ----------------
    ws2 = wb.create_sheet("Instrucciones")
    ws2.sheet_view.showGridLines = False
    ws2.column_dimensions["B"].width = 110
    lineas = [
        ("MARCADOR DE BOLICHE - SISTEMA PROGRAMABLES", True),
        ("", False),
        ("ESTRUCTURA DEL ARCHIVO", True),
        ("Hoja 'Marcador': 4 bloques de jugador (Jugador 1 a 4). Cada jugador tiene:", False),
        ("  - Fila 'frames': números de frame (1 al 10).", False),
        ("  - Fila 'Lanzamientos': ÚNICA fila a cargar. Celdas donde se escriben los pinos derribados en cada lanzamiento.", False),
        ("  - Fila oculta de puntos: cálculo intermedio por frame (no editar).", False),
        ("  - Fila de puntaje (azul clara): puntaje acumulado automático por frame.", False),
        ("  - Celda TOTAL: puntaje final de la partida.", False),
        ("", False),
        ("REGLAS DE PUNTUACIÓN IMPLEMENTADAS", True),
        ("1. Cada partida tiene 10 frames.", False),
        ("2. Strike = 10 pinos con el primer lanzamiento. Vale 10 + los dos lanzamientos siguientes.", False),
        ("3. Spare = 10 pinos en dos lanzamientos. Vale 10 + el lanzamiento siguiente.", False),
        ("4. Frame abierto = suma normal de los dos lanzamientos.", False),
        ("5. Frame 10: con strike o spare se lanzan 3 bolas; sin bonus solo 2.", False),
        ("6. El puntaje acumulado solo se muestra cuando el frame y sus bonificaciones están completos.", False),
        ("", False),
        ("CÓMO CARGAR UNA JUGADA", True),
        ("Ejemplo frame 3 con STRIKE: en las celdas del frame 3 escribir 10 y dejar la 2da vacía.", False),
        ("Ejemplo frame 4 con SPARE 7-3: escribir 7 en la 1ra celda y 3 en la 2da.", False),
        ("Ejemplo frame 5 abierto 4-5: escribir 4 y 5. El acumulado se suma solo.", False),
        ("", False),
        ("INTEGRACIÓN CON LA CÁMARA IA (próximo paso)", True),
        ("La cámara detectará los pinos derribados por lanzamiento. El flujo será:", False),
        ("  1. Captura de imagen -> modelo de visión (YOLO u otro) -> cantidad de pinos derribados.", False),
        ("  2. Ese entero (0 a 10) se escribe en la celda correspondiente del Excel (openpyxl o similar).", False),
        ("  3. El Excel recalcula automáticamente el marcador con las reglas oficiales.", False),
        ("El script 'generar_marcador.py' genera este archivo; se puede extender para escribir", False),
        ("lanzamientos programáticamente desde el software de la cámara.", False),
    ]
    for i, (txt, bold) in enumerate(lineas, start=1):
        c = ws2.cell(i, 2, txt)
        c.font = Font(bold=bold, size=12 if bold and i == 1 else 11,
                      color=AZUL if bold else "333333")
        c.alignment = Alignment(wrap_text=False)

    wb.save(ruta)
    print(f"Archivo generado: {ruta}")


if __name__ == "__main__":
    import os

    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "marcador_boliche.xlsx")
    crear_excel(ruta)
