"""Classifica um anúncio numa categoria + tipo (bom/pecas). Devolve None se não for 190E/260E."""
import re

CATS = ["190E 1.8", "190E 2.0", "190E 2.3 8v", "190E 2.3 12v",
        "190E 2.5 12v", "190E 2.6", "260E", "190E 16v"]
REVER = "A rever"

PECAS = ["peças", "pecas", "desmontar", "desmontagem", "sucata", "não anda", "nao anda",
         "motor avariado", "para restauro", "p/ restauro", "abate", "só peças", "so pecas",
         "vendo em peças", "acidentado", "sinistrado"]
DIESEL = [r"\b190\s?d\b", r"\b2\.0\s?d\b", r"\b2\.5\s?d\b", r"\b2\.5\s?td\b", "diesel", "gasóleo", "gasoleo"]


def _has(txt, pats):
    return any(re.search(p, txt) for p in pats)


def classify(title, desc=""):
    t = f"{title} {desc}".lower()
    t = t.replace(",", ".")
    ttl = title.lower().replace(",", ".")

    is260 = bool(re.search(r"\b260\s?-?e\b", t))
    is190 = bool(re.search(r"\b190\s?-?e\b|\bw201\b", t)) or (
        re.search(r"\b190\b", ttl) and re.search(r"mercedes|benz", t))
    if not (is260 or is190):
        return None
    if is190 and not is260 and _has(ttl, DIESEL):
        return None  # 190D / diesel: excluído

    kind = "pecas" if any(k in t for k in PECAS) else "bom"
    if is260 and not is190:
        return {"cat": "260E", "kind": kind}

    if re.search(r"2\.[35]\s?-?16|cosworth|evolution|\bevo\b|\b16\s?v", t):
        cat = "190E 16v"
    elif re.search(r"\b2\.6\b", t):
        cat = "190E 2.6"
    elif re.search(r"\b2\.5\b", t):
        cat = "190E 2.5 12v"
    elif re.search(r"\b2\.3\b", t):
        if re.search(r"\b12\s?v", t):
            cat = "190E 2.3 12v"
        elif re.search(r"\b8\s?v", t):
            cat = "190E 2.3 8v"
        else:
            return {"cat": REVER, "kind": kind, "hint": "2.3 sem indicar 8v/12v"}
    elif re.search(r"\b2\.0\b", t):
        cat = "190E 2.0"
    elif re.search(r"\b1\.8\b", t):
        cat = "190E 1.8"
    else:
        return {"cat": REVER, "kind": kind, "hint": "Falta a motorização"}
    return {"cat": cat, "kind": kind}


if __name__ == "__main__":
    tests = ["Mercedes 190E 1.8 manual", "190E 2.0 para peças", "Mercedes 190E 2.3 8v",
             "190 E 2.3 12v raro", "Mercedes 190E 2.5-16 Evolution", "190E 2.6 automático",
             "Mercedes 260E W124", "Mercedes W201 antigo", "Mercedes 190E 2.3 gasolina",
             "Mercedes 190 D diesel", "Honda Civic", "Mercedes 190 gasolina clássico"]
    for x in tests:
        print(f"{x:40} -> {classify(x)}")
