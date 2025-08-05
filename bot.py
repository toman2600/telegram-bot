import asyncio
import requests
from telegram import Bot
from datetime import datetime, timedelta

# 🔧 Настройки
TELEGRAM_TOKEN = '8227455166:AAEEbMRFJ1apJMm7Si1IoIYk0bJBL9Xl1Gw'
CHAT_ID = -1002650360570
ACCOUNT_NAME = 'adrop.iu'
POLL_INTERVAL = 15

EOS_API = f'https://eos.hyperion.eosrio.io/v2/history/get_actions?account={ACCOUNT_NAME}&limit=10'
BALANCE_API = 'https://eos.greymass.com/v1/chain/get_currency_balance'

seen_tx_ids = set()

def get_token_balance(account, symbol='A', contract='eosio.token'):
    try:
        resp = requests.post(BALANCE_API, json={
            "account": account,
            "code": contract,
            "symbol": symbol
        })
        arr = resp.json()
        return arr[0] if arr else f"0.0000 {symbol}"
    except Exception as e:
        print("❌ Ошибка при получении баланса:", e)
        return f"0.0000 {symbol}"

def get_current_time_gmt_plus3():
    now_utc = datetime.utcnow()
    gmt_plus3 = now_utc + timedelta(hours=3)
    return gmt_plus3.strftime("%Y-%m-%d %H:%M:%S")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Бот запущен и работает.")

    while True:
        try:
            res = requests.get(EOS_API).json()
            for action in res.get('actions', []):
                tx_id = action.get('trx_id')
                if not tx_id or tx_id in seen_tx_ids:
                    continue

                data = action.get('act', {}).get('data', {})
                symbol = data.get('symbol', '')
                quantity = data.get('quantity', '')

                if symbol != 'A' and not quantity.endswith(' A'):
                    continue

                from_account = data.get('from', '')
                to_account = data.get('to', '')
                memo = data.get('memo', '')

                direction = ""
                emoji = ""
                if to_account == ACCOUNT_NAME:
                    direction = "✔️ *Входящая транзакция:*"
                elif from_account == ACCOUNT_NAME:
                    direction = "💸 *Исходящая транзакция:*"
                else:
                    continue  # Не наша транзакция

                balance = get_token_balance(ACCOUNT_NAME)
                timestamp = get_current_time_gmt_plus3()

                msg = (
                    f"🕒 `{timestamp}`\n"
                    f"{direction}\n"
                    f"*Quantity:* `{quantity}`\n"
                    f"*From:* `{from_account}`\n"
                    f"*To:* `{to_account}`\n"
                    f"*Memo:* `{memo}`\n\n"
                    f"*A balance:* `{balance}`"
                )
                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
                seen_tx_ids.add(tx_id)

        except Exception as e:
            print("❌ Ошибка:", e)

        await asyncio.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
