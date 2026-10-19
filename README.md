# Radar 190E / 260E

Recolhe anúncios (OLX, Standvirtual; Custojusto e PiscaPisca por implementar), classifica por motorização
e avisa no Telegram. Corre no GitHub Actions de 30 em 30 min e guarda tudo em `data/anuncios.json`.

## Instalar
1. Telegram: fala com @BotFather, `/newbot`, guarda o token. Envia uma mensagem ao teu bot e abre
   `https://api.telegram.org/bot<TOKEN>/getUpdates` para ver o teu `chat.id`.
2. GitHub: cria um repositório **privado**, faz upload destes ficheiros.
3. Settings > Secrets and variables > Actions > Secrets: `TELEGRAM_TOKEN` e `TELEGRAM_CHAT_ID`.
   (Opcional, em Variables: `MAX_PRICE`, ex. 15000.)
4. Separador Actions > "Recolher anúncios" > Run workflow. Vê os logs.

## Testar a classificação
`python collector/classify.py`
