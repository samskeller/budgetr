#! /usr/bin/env python

import csv
import json

from parse_transactions_utils import bucket_transactions
from parsing_utils import parse_args, get_date_from_filename
from plot import output_month_plot

def main():
    parsed_args = parse_args()

    with parsed_args.month_csv as month_csv:
        date = get_date_from_filename(parsed_args.month_csv.name)
        headers = [h.strip() for h in parsed_args.month_csv.readline().split(',')]
        csv_reader = csv.DictReader(parsed_args.month_csv, fieldnames=headers)

        monthly_totals, transactions = bucket_transactions(csv_reader)

    month_string = date.strftime('%Y-%m')
    try:
        output_filename = f"outputs/{month_string}-output.json"
        with open(output_filename, 'w') as output_file:
            output = {"totals": monthly_totals, "transactions": transactions}
            output_file.write(json.dumps(output, indent=2, sort_keys=True))
    except IOError:
        logging.exception("Cannot write the output file")
        sys.exit()

    with parsed_args.totals_file as totals_file:
        totals = json.loads(totals_file.read())
        totals["months"][month_string] = monthly_totals
        overall_totals = {}
        for month_string, month in totals["months"].items():
            for category, amount in month.items():
                overall_totals[category] = overall_totals.get(category, 0) + amount
        averages = {category: amount / len(totals["months"]) for category, amount in overall_totals.items()}
        totals["averages"] = averages
        totals_file.seek(0)
        totals_file.write(json.dumps(totals, indent=2, sort_keys=True))
        totals_file.truncate()

    output_month_plot(monthly_totals, averages, month_string)

if __name__ == '__main__':
    main()
