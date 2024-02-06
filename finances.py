import argparse
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta

from monarchmoney import MonarchMoney


async def print_balances(mm: MonarchMoney):
    """Print all account balances fetched from Monarch."""
    data = await mm.get_accounts()
    accounts = sorted(data['accounts'], key=lambda a: a['displayName'])

    for a in accounts:
        if a['includeInNetWorth']:
            account = a['displayName']
            balance = a['currentBalance'] if a['currentBalance'] else a['displayBalance']
            print(f'{account}\t{balance}')


async def print_expenses(mm: MonarchMoney, date: datetime):
    """Print all account expenses fetched from Monarch."""
    start_date = date.replace(day=1)
    end_date = (date.replace(month=date.month % 12 + 1, year=date.year + (date.month // 12)) - timedelta(days=1))

    offset = 0
    result = defaultdict(list)
    while True:
        data = await mm.get_transactions(start_date=start_date.strftime('%Y-%m-%d'),
                                         end_date=end_date.strftime('%Y-%m-%d'), offset=offset)

        if len(data['allTransactions']['results']) == 0:
            break

        for t in data['allTransactions']['results']:
            if t['category']['name'] in ('Transfer', 'Credit Card Payment') or t['amount'] > 0:
                continue

            account = t['account']['displayName']

            result[account].append({
                'day': t['date'].split('-')[2],
                'category': t['category']['name'],
                'merchant': t['merchant']['name'],
                'amount': abs(t['amount']),
            })

        offset += len(data['allTransactions']['results'])

    sorted_accounts = sorted(result.keys())
    for account in sorted_accounts:
        transactions = result[account]
        sorted_transactions = sorted(transactions, key=lambda x: x['day'])

        print(account)
        for t in sorted_transactions:
            print(f"{t['day']}\t{t['category']}\t{t['merchant']}\t{t['amount']}")


async def main():
    """Entrypoint for printing expenses or balances."""
    parser = argparse.ArgumentParser(description='Process some financial data.')
    parser.add_argument('--type', type=str, choices=['expenses', 'balances'], required=True)
    parser.add_argument('--date', type=lambda s: datetime.strptime(s, '%Y-%m-%d'), required=True)
    args = parser.parse_args()

    mm = MonarchMoney()
    try:
        mm.load_session()
    except Exception as e:
        print(f'Failed to load session due to {e}, attempting interactive login...')
        await mm.interactive_login()

    if args.type == 'expenses':
        await print_expenses(mm, args.date)
    elif args.type == 'balances':
        await print_balances(mm)


asyncio.run(main())
