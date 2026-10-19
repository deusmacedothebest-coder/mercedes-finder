"""Fontes de anúncios. Cada fonte devolve uma lista de dicts:
{id, source, title, desc, price, year, km, region, url}
NOTA: estas fontes ainda NÃO foram testadas contra os sites reais (o ambiente onde foram escritas
não tem acesso a eles). Na primeira execução, vê os logs do GitHub Actions e ajusta se for preciso."""
import json, re, requests

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36",
      "Accept-Language": "pt-PT,pt;q=0.9"}
QUERIES = ["mercedes 190e", "mercedes 260e", "mercedes w201", "mercedes 190 gasolina"]


def olx():
    out = []
    for q in QUERIES:
        r = requests.get("https://www.olx.pt/api/v1/offers/", headers=UA, timeout=30,
                         params={"offset": 0, "limit": 40, "query": q, "sort_by": "created_at:desc"})
        r.raise_for_status()
        for o in r.json().get("data", []):
            price = None
            for p in o.get("params", []):
                if p.get("key") == "price":
                    price = (p.get("value") or {}).get("value")
            out.append({"id": f"olx-{o['id']}", "source": "OLX", "title": o.get("title", ""),
                        "desc": re.sub(r"<[^>]+>", " ", o.get("description", "")),
                        "price": price, "year": None, "km": None,
                        "region": ((o.get("location") or {}).get("city") or {}).get("name", ""),
                        "url": o.get("url", "")})
    return out


def _walk(node, found):
    """Procura recursivamente objetos que pareçam anúncios dentro do JSON da página."""
    if isinstance(node, dict):
        if node.get("title") and (node.get("url") or node.get("slug")) and node.get("id"):
            found.append(node)
        for v in node.values():
            _walk(v, found)
    elif isinstance(node, list):
        for v in node:
            _walk(v, found)


def standvirtual():
    out = []
    for q in QUERIES:
        r = requests.get("https://www.standvirtual.com/carros",
                         headers=UA, timeout=30,
                         params={"search[filter_search]": q, "search[order]": "created_at_first:desc"})
        r.raise_for_status()
        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S)
        if not m:
            print("standvirtual: __NEXT_DATA__ não encontrado (site mudou ou bloqueou)")
            continue
        found = []
        _walk(json.loads(m.group(1)), found)
        for o in found:
            price = o.get("price")
            if isinstance(price, dict):
                price = (price.get("amount") or {}).get("units") or price.get("value")
            out.append({"id": f"sv-{o['id']}", "source": "Standvirtual", "title": str(o["title"]),
                        "desc": str(o.get("shortDescription", "")), "price": price,
                        "year": None, "km": None, "region": "", "url": o.get("url") or o.get("slug")})
    return out


# Ainda por implementar: precisam de ver o HTML real primeiro.
def custojusto():
    return []


def piscapisca():
    return []


SOURCES = {"OLX": olx, "Standvirtual": standvirtual, "Custojusto": custojusto, "PiscaPisca": piscapisca}
