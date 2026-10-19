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
    """custojusto.pt: páginas de modelo e de pesquisa de texto, nacionais."""
    import html as H
    out, seen = [], set()
    base = "https://www.custojusto.pt"
    paths = ["/portugal/veiculos/carros-usados/mercedes-benz/190",
             "/portugal/veiculos/carros-usados/q/mercedes%20190e",
             "/portugal/veiculos/carros-usados/q/mercedes%20260e",
             "/portugal/veiculos/carros-usados/q/mercedes%20w201"]
    for p in paths:
        r = requests.get(base + p, headers=UA, timeout=30)
        if r.status_code == 404:
            continue
        r.raise_for_status()
        for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S):
            href, inner = m.group(1), m.group(2)
            idm = re.search(r"/veiculos/[^?\"]*-(\d{6,})(?:\?|$)", href)
            title = H.unescape(re.sub(r"<[^>]+>", " ", inner)).strip()
            if not idm or not title or idm.group(1) in seen:
                continue  # ignora links só com imagem e repetidos
            seen.add(idm.group(1))
            nxt = r.text.find("<h2", m.end())
            end = min(nxt if nxt != -1 else m.end() + 700, m.end() + 700)
            seg = H.unescape(re.sub(r"<[^>]+>", " ", r.text[m.end():end]))
            seg = re.sub(r"\s+", " ", seg)
            pm = re.search(r"([\d][\d\s\u00a0]*)\s*€", seg)
            rm = re.search(r"·\s*(\d{4})\s+(.+?)\s+[\d][\d\s\u00a0]*\s*€", seg)
            url = href.split("?")[0]
            url = url if url.startswith("http") else base + url
            out.append({"id": f"cj-{idm.group(1)}", "source": "Custojusto", "title": title,
                        "desc": seg[:200], "price": int(re.sub(r"\D", "", pm.group(1))) if pm else None,
                        "year": int(rm.group(1)) if rm else None, "km": None,
                        "region": re.sub(r"^ou anterior\s*", "", rm.group(2)) if rm else "", "url": url})
    return out


def piscapisca():
    return []


def auto_moto():
    """auto.moto.pt: uma página por modelo, HTML simples com um link por anúncio."""
    import html as H
    out, seen = [], set()
    base = "https://auto.moto.pt"
    for path in ["/carros/mercedes-benz/190-e", "/carros/mercedes-benz/190",
                 "/carros/mercedes-benz/260-e", "/carros/mercedes-benz/260"]:
        r = requests.get(base + path, headers=UA, timeout=30)
        if r.status_code == 404:
            continue  # esse modelo pode não ter página
        r.raise_for_status()
        for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", r.text, re.S):
            attrs, inner = m.group(1), m.group(2)
            h = re.search(r'href="([^"]+)"', attrs)
            if not h:
                continue
            idm = re.search(r"/carros/[^/]+/mercedes-benz/[^/]+/[^/]+/(\d+)$", h.group(1))
            if not idm or idm.group(1) in seen:
                continue
            seen.add(idm.group(1))
            t = re.search(r'title="([^"]+)"', attrs)
            title = H.unescape(t.group(1)) if t else ""
            text = H.unescape(re.sub(r"<[^>]+>", " ", inner))
            pm = re.search(r"([\d][\d\s\u00a0.]*)\s*EUR", text)
            km = re.search(r"([\d][\d\s\u00a0]*)\s*km", title)
            region = title.split("·")[-1].strip() if "·" in title else ""
            url = h.group(1) if h.group(1).startswith("http") else base + h.group(1)
            out.append({"id": f"am-{idm.group(1)}", "source": "AutoMoto",
                        "title": title.split(" — ")[0], "desc": text,
                        "price": int(re.sub(r"\D", "", pm.group(1))) if pm else None,
                        "year": None, "km": int(re.sub(r"\D", "", km.group(1))) if km else None,
                        "region": region, "url": url})
    return out


SOURCES = {"AutoMoto": auto_moto, "OLX": olx, "Standvirtual": standvirtual, "Custojusto": custojusto, "PiscaPisca": piscapisca}
