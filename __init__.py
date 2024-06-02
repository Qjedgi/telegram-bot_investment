import asyncio
import os
from datetime import datetime, timedelta
from tinkoff.invest import AsyncClient
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
TOKEN = os.environ["TOKEN_TINKOFF"]

async def main():
    async with AsyncClient(TOKEN) as client:
        accounts = await client.users.get_accounts()
        operations = []

        for account in accounts.accounts:
            operations_response = await client.operations.get_operations(
                account_id=account.id,
                from_=datetime(2023, 9, 1),
                to=datetime.now()
            )

            for operation in operations_response.operations:
                operations.append({
                    "type": operation.type,
                    "payment": operation.payment.units + operation.payment.nano / 10**9
                })

        # Группировка и суммирование операций по типу
        summary = {}
        for operation in operations:
            if operation["type"] not in summary:
                summary[operation["type"]] = 0
            summary[operation["type"]] += operation["payment"]

        # Вывод данных в консоль
        print("Summary:")
        for key, value in summary.items():
            print(f"{key}: {value}")

        # Общий итог
        total = sum(summary.values())
        print(f"Total: {total}")

if __name__ == "__main__":
    asyncio.run(main())