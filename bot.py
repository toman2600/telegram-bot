import asyncio
import requests
from telegram import Bot

# 🔧 Настройки
TELEGRAM_TOKEN = '8227455166:AAEEbMRFJ1apJMm7Si1IoIYk0bJBL9Xl1Gw'
CHAT_ID = -1002650360570  # Замени на свой
ACCOUNT_NAME = 'adrop.iu'
POLL_INTERVAL = 30  # Проверка каждые 30 секунд

EOS_API = f'https://eos.hyperion.eosrio.io/v2/history/get_actions?account={ACCOUNT_NAME}&limit=10'

# 🧠 Храним уже обработанные транзакции
seen_tx_ids = set()

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)

    # 🚀 Тестовое сообщение при запуске
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Бот успешно запущен и готов к мониторингу транзакций.")

    while True:
        try:
            response = requests.get(EOS_API)
            data = response.json()

            actions = data.get('actions', [])
            new_txs = []

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
                memo = act_data.get('memo', '')

                msg = f"📥 *Новая транзакция:*\n" \
                      f"*Quantity:* `{quantity}`\n" \
                      f"*From:* `{from_account}`\n" \
                      f"*To:* `{to_account}`\n" \
                      f"*Memo:* `{memo}`"

                await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")

                new_txs.append(tx_id)

            seen_tx_ids.update(new_txs)

            if new_txs:
                print(f"👀 Найдено {len(new_txs)} новых транзакций")

        except Exception as e:
            print(f"⚠️ Ошибка при получении или обработке данных: {e}")

        await asyncio.sleep(POLL_INTERVAL)

# 🚀 Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
