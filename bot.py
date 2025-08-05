import asyncio
import requests
from telegram import Bot

# 🔧 Настройки
TELEGRAM_TOKEN = '8227455166:AAEEbMRFJ1apJMm7Si1IoIYk0bJBL9Xl1Gw'
CHAT_ID = -1002650360570  # Замени на свой
ACCOUNT_NAME = 'adrop.iu'
POLL_INTERVAL = 30  # Проверка каждые 30 секунд

EOS_ACTIONS_API = f'https://eos.hyperion.eosrio.io/v2/history/get_actions?account={ACCOUNT_NAME}&limit=10'
EOS_BALANCE_API = 'https://eos.greymass.com/v1/chain/get_currency_balance'

# 🧠 Храним уже обработанные транзакции
seen_tx_ids = set()

# 🔍 Получение баланса токена A
def get_token_balance(account_name, token_symbol='A', contract='eosio.token'):
    try:
        response = requests.post(EOS_BALANCE_API, json={
            "account": account_name,
            "code": contract,
            "symbol": token_symbol
        })
        balances = response.json()
        return balances[0] if balances else f"0.0000 {token_symbol}"
    except Exception as e:
        print(f"⚠️ Ошибка при получении баланса: {e}")
        return f"не удалось получить баланс"

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)

    # 🚀 Тестовое сообщение при запуске
    await bot.send_message(chat_id=CHAT_ID, text="🚀 Бот успешно запущен и готов к мониторингу транзакций.")

    while True:
        try:
            response = requests.get(EOS_ACTIONS_API)
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

                # 📊 Получаем текущий баланс
                balance = get_token_balance(ACCOUNT_NAME)

                msg = (
                    f"📥 *Новая транзакция:*\n"
                    f"*Quantity:* `{quantity}`\n"
                    f"*From:* `{from_account}`\n"
                    f"*To:* `{to_account}`\n"
                    f"*Memo:* `{memo}`\n\n"
                    f"*A balance:* `{balance}`"
                )

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
