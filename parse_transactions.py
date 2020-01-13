#! /usr/bin/env python

import argparse
import csv
import json

def load_categories():
    try:
        with open('categories.json', 'r') as input_categories:
            return json.loads(input_categories.read())
    except IOError:
        logging.exception("Cannot read the categories file")
        sys.exit()

def bucket_transactions(csv_reader):
    categories_blob = load_categories()

    totals = {category: 0 for category in categories_blob["internalCategories"]}
    category_lookup = categories_blob["categoryMapper"]
    for row in csv_reader:
        try:
            capital_one_category = category_lookup[row["Category"]]
            if isinstance(capital_one_category, str):
                category = capital_one_category
            else:
                category = capital_one_category[row["Description"]]
        except KeyError:
            # TODO: Can't find category, later attempt to create
            category = "Other"

        if row["Credit"]:
            if row["Description"] == "CAPITAL ONE AUTOPAY PYMT":
                continue
            # TODO: Ask the user what to do here
            continue

        totals[category] += float(row["Debit"])

    return totals

def parse_args():
    parser = argparse.ArgumentParser(description="Create a budget")
    parser.add_argument("month_csv", help="Input CSV file with transactions for a month")
    return parser.parse_args()

def main():
    parsed_args = parse_args()

    try:
        with open(parsed_args.month_csv, 'r') as input_csv:
            headers = [h.strip() for h in input_csv.readline().split(',')]
            csv_reader = csv.DictReader(input_csv, fieldnames=headers)

            return bucket_transactions(csv_reader)
    except IOError:
        logging.exception("Cannot read the input file")
        sys.exit()

if __name__ == '__main__':
    print(main())
