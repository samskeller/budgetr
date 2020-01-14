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

def determine_category(row, possibleCategories):
    category_options_string = "\n".join([f"{num}: {category}" for num, category in enumerate(possibleCategories, 1)])
    user_input_options = [str(i) for i in range(1, len(possibleCategories) + 1)]

    prompt = f"\nPick a category for {row['Description']}:\n{category_options_string}\n\n"
    user_selected_category = input(prompt)
    while user_selected_category not in user_input_options:
        print("Sorry, that's not an option. Try again!")
        user_selected_category = input(prompt)

    return possibleCategories[int(user_selected_category) - 1]

def bucket_transactions(csv_reader):
    categories_blob = load_categories()

    totals = {category: 0 for category in categories_blob["internalCategories"]}
    category_lookup = categories_blob["categoryMapper"]
    for row in csv_reader:
        if row["Credit"]:
            if row["Description"] == "CAPITAL ONE AUTOPAY PYMT":
                continue
            # TODO: Ask the user what to do here
            continue

        try:
            capital_one_category = category_lookup[row["Category"]]
            if isinstance(capital_one_category, str):
                category = capital_one_category
            else:
                category = capital_one_category[row["Description"]]
        except KeyError:
            category = determine_category(row, categories_blob["internalCategories"])
            category = "Other"

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
