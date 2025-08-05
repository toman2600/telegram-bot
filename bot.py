import asyncio
import requests
from telegram import Bot
from datetime import datetime, timedelta

# 🔧 Настройки
TELEGRAM_TOKEN = '8227455166:AAEEbMRFJ1apJMm7Si1IoIYk0bJBL9Xl1Gw'
CHAT_ID = -1002650360570  # Замени на свой
ACCOUNT_NAME = 'adrop.iu'
POLL_INTERVAL = 10  # Проверка каждые 30 секунд

EOS_ACTIONS_API = f'https://eos.hyperion.eosrio.io/v2/history/get_actions?account={ACCOUNT_NAME}&limit=10'
EOS_BALANCE_API = f'https://eos.hyperion.eosrio.io/v1/chain/get_currency_balance'

seen_tx_ids = set()
memo_counter_by_date = {}  # { '2025-08-05': { 'memo1': count, 'memo2': count } }

def get_gmt3_time():
    return datetime.utcnow() + timedelta(hours=3)

def get_current_date_str():
    return get_gmt3_time().date().isoformat()

def calculate_plus_4_percent(quantity_str):
    try:
        amount = float(quantity_str.split()[0])
        return round(amount * 1.04, 4)
    except:
        return None

def get_a_balance(account_name):
    try:
        payload = {
            "account": account_name,
            "code": "a.token",
            "symbol": "A"
        }
        response = requests.post(EOS_BALANCE_API, json=payload, timeout=10)
        balance_list = response.json()
        for b in balance_list:
            if b.endswith(" A"):
                return b
        return "0.0000 A"
    except Exception as e:
        print(f"Ошибка при получении баланса: {e}")
        return "0.0000 A"

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Бот успешно запущен и готов к мониторингу транзакций.")

    while True:
        try:
            response = requests.get(EOS_ACTIONS_API)
            data = response.json()

            actions = data.get('actions', [])
            new_txs = []

            current_date = get_current_date_str()
            if current_date not in memo_counter_by_date:
                memo_counter_by_date.clear()  # сбрасываем старые
                memo_counter_by_date[current_date] = {}

            for action in actions:
                tx_id = action.get('trx_id')
                if not tx_id or tx_id in seen_tx_ids:
                    continue

                act_data = action.get('act', {}).get('data', {})
                symbol = act_data.get('symbol', '')
                quantity = act_data.get('quantity', '')

                if symbol != 'A' and not quantity.endswith(' A'):
                    continue

                from_account = act_data.get('from', '')
                to_account = act_data.get('to', '')
                memo = act_data.get('memo', '') or 'без memo'

                direction = 'incoming' if to_account == ACCOUNT_NAME else 'outgoing'

                timestamp = get_gmt3_time().strftime("%Y-%m-%d %H:%M:%S")
                balance = get_a_balance(ACCOUNT_NAME)

                message = f"📅 {timestamp}\n"

                if direction == 'incoming':
                    message += "✔️ *Входящая транзакция:*\n"
                    plus4 = calculate_plus_4_percent(quantity)
                    if plus4:
                        message += f"*Quantity:* `{quantity}` (`{plus4} A`)\n"
                    else:
                        message += f"*Quantity:* `{quantity}`\n"

                    # Считаем memo
                    memo_data = memo_counter_by_date[current_date]
                    count = memo_data.get(memo, 0) + 1
                    memo_data[memo] = count

                    message += f"*From:* `{from_account}`\n"
                    message += f"*To:* `{to_account}`\n"
                    message += f"*Memo:* `{memo}`\n"
                    message += f"🔢 Транзакция {count} из 5\n"

                else:
                    message += "💸 *Исходящая транзакция:*\n"
                    message += f"*Quantity:* `{quantity}`\n"
                    message += f"*From:* `{from_account}`\n"
                    message += f"*To:* `{to_account}`\n"
                    message += f"*Memo:* `{memo}`\n"

                message += f"\n💰 *A balance:* `{balance}`"

                await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
                new_txs.append(tx_id)

            seen_tx_ids.update(new_txs)

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")

        await asyncio.sleep(POLL_INTERVAL)

# 🚀 Запуск
if __name__ == '__main__':
    asyncio.run(main())
