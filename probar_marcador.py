# -*- coding: utf-8 -*-
"""Prueba las formulas del marcador con un mini-evaluador de subconjunto de Excel."""
import math
import re
import sys

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter, column_index_from_string

RUTA = r"C:\Users\anton\Boliche\marcador_boliche.xlsx"
wb = load_workbook(RUTA)
ws = wb["Marcador"]


class CeldaVacia:
    pass


VACIA = CeldaVacia()
valores = {}
_cache_global = [{}]


def val(cell_ref, valores):
    v = valores.get(cell_ref, VACIA)
    return v


# --- Parser/evaluador de formulas (subconjunto) ---
TOKEN = re.compile(r"""
    (?P<str>"[^"]*")
  | (?P<func>[A-Z]+(?=\())
  | (?P<ref>\$?[A-Z]{1,3}\$?\d+)
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<op><=|>=|<>|=|<|>|\+|-|\(|\)|,)
""", re.X)


def tokenize(s):
    toks = []
    pos = 0
    while pos < len(s):
        if s[pos].isspace():
            pos += 1
            continue
        m = TOKEN.match(s, pos)
        if not m:
            raise ValueError(f"Token inesperado en {s[pos:pos+20]!r}")
        toks.append((m.lastgroup, m.group()))
        pos = m.end()
    return toks


class Parser:
    def __init__(self, toks, valores):
        self.toks = toks
        self.i = 0
        self.valores = valores

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def next(self):
        t = self.toks[self.i]
        self.i += 1
        return t

    def expect(self, val):
        k, v = self.next()
        assert v == val, f"esperaba {val} got {v}"

    def parse(self):
        e = self.cmp()
        return e

    def cmp(self):
        left = self.add()
        while self.peek()[1] in ("=", "<", ">", "<=", ">=", "<>"):
            op = self.next()[1]
            right = self.add()
            left = ("cmp", op, left, right)
        return left

    def add(self):
        left = self.atom()
        while self.peek()[1] in ("+", "-"):
            op = self.next()[1]
            right = self.atom()
            left = ("bin", op, left, right)
        return left

    def atom(self):
        k, v = self.next()
        if v == "(":
            e = self.cmp()
            self.expect(")")
            return e
        if k == "num":
            return ("num", float(v))
        if k == "str":
            return ("str", v[1:-1])
        if k == "ref":
            return ("ref", v.replace("$", ""))
        if k == "func":
            self.expect("(")
            args = []
            if self.peek()[1] != ")":
                args.append(self.cmp())
                while self.peek()[1] == ",":
                    self.next()
                    args.append(self.cmp())
            self.expect(")")
            return ("func", v, args)
        raise ValueError(f"no esperaba {v}")


def excel_num(v):
    if isinstance(v, CeldaVacia) or v is None or v == "":
        return 0.0
    if isinstance(v, str):
        return 0.0
    return float(v)


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def ev(node):
    t = node[0]
    if t == "num":
        return node[1]
    if t == "str":
        return node[1]
    if t == "ref":
        return resolver(node[1])
    if t == "bin":
        a, b = ev(node[2]), ev(node[3])
        if node[1] == "+":
            return excel_num(a) + excel_num(b)
        return excel_num(a) - excel_num(b)
    if t == "cmp":
        a, b = ev(node[2]), ev(node[3])
        # Excel: celda vacia comparada con "" da TRUE; con numeros vale 0
        if isinstance(a, CeldaVacia):
            a = "" if isinstance(b, str) else 0.0
        if isinstance(b, CeldaVacia):
            b = "" if isinstance(a, str) else 0.0
        if isinstance(a, str) or isinstance(b, str):
            if not isinstance(a, str):
                a = excel_num(a)
            if not isinstance(b, str):
                b = excel_num(b)
        op = node[1]
        return {"=": a == b, "<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b, "<>": a != b}[op]
    if t == "func":
        name, args = node[1], node[2]
        if name == "IF":
            cond = ev(args[0])
            return ev(args[1]) if cond else (ev(args[2]) if len(args) > 2 else False)
        if name == "AND":
            return all(ev(a) for a in args)
        if name == "OR":
            return any(ev(a) for a in args)
        if name == "NOT":
            return not ev(args[0])
        if name == "ISNUMBER":
            v = ev(args[0])
            if isinstance(v, CeldaVacia):
                return False
            return is_number(v) and v != "" if not isinstance(v, str) else False
        raise ValueError(f"funcion desconocida {name}")
    raise ValueError(node)


def eval_cell(coord, valores, cache):
    if coord in cache:
        return cache[coord]
    f = ws[coord].value
    if not isinstance(f, str) or not f.startswith("="):
        cache[coord] = f if f is not None else VACIA
        return cache[coord]
    toks = tokenize(f[1:])
    p = Parser(toks, valores)
    r = ev(p.parse())
    cache[coord] = r
    return r


def evaluar_jugador(fila_lanz, fila_puntos, fila_acum, lanzamientos):
    """lanzamientos: dict (frame,lanz)->valor o None"""
    global valores, _cache_global
    valores = {}
    cache = {}
    _cache_global = [cache]
    for (fr, ln), v in lanzamientos.items():
        col = get_column_letter(2 + (2 * (fr - 1) + ln - 1) if fr < 10 else 20 + ln - 1)
        if v is not None:
            valores[f"{col}{fila_lanz}"] = v
    puntos = {}
    for fr in range(1, 11):
        col = get_column_letter(2 + 2 * (fr - 1) if fr < 10 else 20)
        c = eval_cell(f"{col}{fila_puntos}", valores, cache)
        puntos[fr] = c
    acum = {}
    for fr in range(1, 11):
        col = get_column_letter(2 + 2 * (fr - 1) if fr < 10 else 20)
        c = eval_cell(f"{col}{fila_acum}", valores, cache)
        acum[fr] = c
    total = eval_cell(f"W{fila_acum}", valores, cache)
    return puntos, acum, total


def resolver(coord):
    return eval_cell(coord, valores, _cache_global[0])


def next_real(lanzamientos, flat_cells, start_pos, count):
    got = []
    p = start_pos
    while len(got) < count and p < len(flat_cells):
        gg, kk = flat_cells[p]
        v = lanzamientos.get((gg, kk))
        if v is not None:
            got.append(v)
        p += 1
    return got


def referencia_total(lanzamientos):
    """Puntaje esperado con implementacion pura de reglas de boliche."""
    flat_cells = []
    for fr in range(1, 11):
        n = 3 if fr == 10 else 2
        for ln in range(1, n + 1):
            flat_cells.append((fr, ln))
    pos = 0
    total = 0
    acums = []
    for fr in range(1, 11):
        r1 = lanzamientos.get((fr, 1))
        if fr < 10:
            if r1 == 10:
                b = next_real(lanzamientos, flat_cells, pos + 1, 2)
                if len(b) == 2:
                    total += 10 + b[0] + b[1]
                    acums.append(total)
                else:
                    acums.append(None)
                pos += 1
            else:
                r2 = lanzamientos.get((fr, 2))
                if r1 is not None and r2 is not None:
                    if r1 + r2 == 10:
                        b = next_real(lanzamientos, flat_cells, pos + 2, 1)
                        if b:
                            total += 10 + b[0]
                            acums.append(total)
                        else:
                            acums.append(None)
                    else:
                        total += r1 + r2
                        acums.append(total)
                else:
                    acums.append(None)
                pos += 2
        else:
            r2 = lanzamientos.get((fr, 2))
            r3 = lanzamientos.get((fr, 3))
            if r1 is not None and r2 is not None:
                if r1 + r2 >= 10:
                    if r3 is not None:
                        total += r1 + r2 + r3
                        acums.append(total)
                    else:
                        acums.append(None)
                else:
                    total += r1 + r2
                    acums.append(total)
            else:
                acums.append(None)
    return acums, total


FILAS = [(4 + j * 6, 4 + j * 6 + 2, 4 + j * 6 + 3, 4 + j * 6 + 4) for j in range(4)]

casos = []

# Caso 1: perfect game (jugador 1) -> 300
lanz = {}
for fr in range(1, 10):
    lanz[(fr, 1)] = 10
lanz[(10, 1)] = lanz[(10, 2)] = lanz[(10, 3)] = 10
casos.append(("Partida perfecta", 0, lanz, 300))

# Caso 2: todos spares 5-5 con 5 extra -> 150 (jugador 2)
lanz = {}
for fr in range(1, 10):
    lanz[(fr, 1)] = 5
    lanz[(fr, 2)] = 5
lanz[(10, 1)] = 5; lanz[(10, 2)] = 5; lanz[(10, 3)] = 5
casos.append(("Todos spares 5-5", 1, lanz, 150))

# Caso 3: juego mixto conocido: 9,0 7,3 10 9,0 8,1 10 10 7,2 10 X,7,2 -> 161?
# Calcular con referencia: frames:
# f1 9,0=9; f2 7,3 spare +9=29; f3 strike +9+0=48; f4 9,0=57; f5 8,1=66; f6 strike+10+7=93;
# f7 strike+7+2=112; f8 7,2=121; f9 strike+10+7=148; f10 10,7,2=168? recalcule:
lanz = {
    (1,1):9,(1,2):0,
    (2,1):7,(2,2):3,
    (3,1):10,
    (4,1):9,(4,2):0,
    (5,1):8,(5,2):1,
    (6,1):10,
    (7,1):10,
    (8,1):7,(8,2):2,
    (9,1):10,
    (10,1):10,(10,2):7,(10,3):2,
}
acums_esp, total_esp = None, None  # lo calcula la referencia
casos.append(("Juego mixto", 2, lanz, "ref"))

# Caso 4: casi vacio, frame 1 abierto 4,5 -> acum 9
lanz = {(1,1):4,(1,2):5}
casos.append(("Solo frame 1 abierto", 3, lanz, "ref"))

# Caso 5: strike en frame1 y nada mas -> acum vacio
lanz = {(1,1):10}
casos.append(("Strike incompleto", 3, lanz, "ref"))

if __name__ == "__main__":
    fallos = 0
    for nombre, j, lanz, esperado in casos:
        f_nom, f_lanz, f_puntos, f_acum = FILAS[j]
    puntos, acum, total = evaluar_jugador(f_lanz, f_puntos, f_acum, lanz)
    acums_esp, total_esp = referencia_total(lanz)
    if esperado == "ref":
        esp_total = total_esp
    else:
        esp_total = esperado
    # comparar acumulados (None <-> vacio/"")
    ok = True
    for fr in range(1, 11):
        got = acum[fr]
        got_v = None if (got is None or got == "" or got is False) else got
        esp = acums_esp[fr - 1]
        if got_v != esp and not (esp is None and got_v is None):
            ok = False
            print(f"  [{nombre}] frame {fr}: excel={got_v!r} esperado={esp!r}")
    tv = total if (total is not None and total != "" and total is not False) else None
    if tv != esp_total and not (esp_total is None and tv is None):
        ok = False
        print(f"  [{nombre}] TOTAL: excel={tv!r} esperado={esp_total!r}")
    print(f"{'OK ' if ok else 'FALLA'} {nombre}: total excel={tv!r} esperado={esp_total!r}")
    if not ok:
        fallos += 1

# Caso extra: strike doble
lanz = {(1,1):10,(2,1):10,(3,1):10,(4,1):9,(4,2):0}
f_nom, f_lanz, f_puntos, f_acum = FILAS[0]
puntos, acum, total = evaluar_jugador(f_lanz, f_puntos, f_acum, lanz)
esperado_acum = [30, 59, 89, 98]
ok = all(acum[fr] == esperado_acum[fr-1] for fr in range(1,5))
print(f"{'OK ' if ok else 'FALLA'} Tres strikes iniciales: {[acum[fr] for fr in range(1,5)]} esperado {esperado_acum}")
if not ok:
    fallos += 1

sys.exit(1 if fallos else 0)
