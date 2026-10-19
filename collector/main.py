import json, os, sys, time, requests
from pathlib import Path
from classify import classify, REVER
from sources import SOURCES

DATA = Path(__file__).resolve().parent.parent / "data" / "anuncios.json"
TOKEN, CHAT = os.getenv("TELEGRAM_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
MAX_PRICE = int(os.getenv("MAX_PRICE") or 0)  # 0 = sem limite


def telegram(text):
    if not (TOKEN and CHAT):
        print("[sem Telegram configurado]", text); return
    r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", timeout=20,
                      json={"chat_id": CHAT, "text": text, "disable_web_page_preview": False})
    if not r.ok:
        print("Telegram falhou:", r.status_code, r.text)


def main():
    db = {a["id"]: a for a in json.loads(DATA.read_text())}
    first_run = not db
    new, errors = [], []
    for name, fn in SOURCES.items():
        try:
            items = fn()
        except Exception as e:  # uma fonte a falhar não pára as outras
            errors.append(f"{name}: {e}"); print("ERRO", name, e); continue
        print(f"{name}: {len(items)} resultados")
        for it in items:
            c = classify(it["title"], it.get("desc", ""))
            if not c or it["id"] in db:
                continue
            if MAX_PRICE and it.get("price") and float(it["price"]) > MAX_PRICE:
                continue
            it.update(c, first_seen=int(time.time()))
            it.pop("desc", None)
            db[it["id"]] = it; new.append(it)
    DATA.write_text(json.dumps(sorted(db.values(), key=lambda a: -a["first_seen"]),
                               ensure_ascii=False, indent=1))
    if first_run and db:
        telegram(f"Radar 190E/260E ativo. Primeira recolha: {len(db)} anúncios guardados. "
                 "A partir de agora recebes só os novos.")
    elif len(new) > 8:  # muitos de uma vez: um resumo em vez de uma mensagem por anúncio
        lines = []
        for a in sorted(new, key=lambda x: x["cat"]):
            p = f"{a['price']} €" if a.get("price") else "?"
            lines.append(f"{a['cat']} · {p} · {a['title']} ({a.get('region','')})\n{a['url']}")
        msg = f"Radar: {len(new)} anúncios novos\n\n"
        for ln in lines:
            if len(msg) + len(ln) > 3800:
                telegram(msg); msg = ""
            msg += ln + "\n\n"
        telegram(msg)
    else:
        for a in new:
            tag = "PEÇAS" if a["kind"] == "pecas" else ("A REVER" if a["cat"] == REVER else "")
            extra = f"\n({a['hint']})" if a.get("hint") else ""
            p = f"{a['price']} €" if a.get("price") else "preço ?"
            telegram(f"{a['cat']} {tag}\n{a['title']}\n{p} · {a['source']} · {a.get('region','')}{extra}\n{a['url']}")
            time.sleep(1)
    if errors and len(errors) == len(SOURCES):
        telegram("Radar: todas as fontes falharam.\n" + "\n".join(errors)); sys.exit(1)
    print(f"{len(new)} novos")


if __name__ == "__main__":
    main()
