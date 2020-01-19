#! /usr/bin/env python

import argparse
import csv
import datetime
import json

def read_categories():
    try:
        with open('categories.json', 'r') as input_categories:
            return json.loads(input_categories.read())
    except IOError:
        logging.exception("Cannot read the categories file")
        sys.exit()

def write_categories(categories_blob):
    try:
        with open('categories.json', 'w') as output_categories:
            output_categories.write(json.dumps(categories_blob, indent=2, sort_keys=True))
    except IOError:
        logging.exception("Cannot write to the categories file")
        sys.exit()

def parse_user_selected_category(prompt):
    add_category = False
    user_selected_category = input(prompt)
    if user_selected_category[-1] == '+':
        add_category = True
        user_selected_category = user_selected_category[:-1]

    return (user_selected_category, add_category)

def handle_unknown_category(row, possible_categories, category_mapper):
    category_options_string = "\n".join([f"{num}: {category}" for num, category in enumerate(possible_categories, 1)])
    user_input_options = [str(i) for i in range(1, len(possible_categories) + 1)]

    prompt = f"\nPick a category for {row['Description']} (add '+' suffix to save):\n{category_options_string}\n\n"
    user_selected_category, add_category = parse_user_selected_category(prompt)
    while user_selected_category not in user_input_options:
        print("Sorry, that's not an option. Try again!")
        user_selected_category, add_category = parse_user_selected_category(prompt)

    category = possible_categories[int(user_selected_category) - 1]
    if add_category:
        if row["Category"] not in category_mapper:
            category_mapper[row["Category"]] = {}
        category_mapper[row["Category"]][row["Description"]] = category

    return category

def bucket_transactions(csv_reader):
    categories_blob = read_categories()

    totals = {category: 0 for category in categories_blob["internalCategories"]}
    transactions = {category: [] for category in categories_blob["internalCategories"]}
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
            category = handle_unknown_category(row, categories_blob["internalCategories"], category_lookup)

        totals[category] = round(totals[category] + float(row["Debit"]), 2)
        transactions[category].append({"description": row["Description"], "amount": row["Debit"], "date": row["Transaction Date"]})

    # Write category_mapper back to categories.json
    categories_blob["categoryMapper"] = category_lookup
    write_categories(categories_blob)

    return (totals, transactions)

def transaction_file_type(value):
    date_string = value[:len('2020-01-01')]
    try:
        datetime.datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        raise argparse.ArgumentTypeError

    return value

def parse_args():
    parser = argparse.ArgumentParser(description="Create a budget")
    parser.add_argument("month_csv", help="Input CSV file with transactions for a month")
    return parser.parse_args()

def main():
    parsed_args = parse_args()

    try:
        with open(parsed_args.month_csv, 'r') as input_csv:
            filename = input_csv.name.split('/')[-1]
            date = datetime.datetime.strptime(filename[:len('2020-01-01')], '%Y-%m-%d')
            headers = [h.strip() for h in input_csv.readline().split(',')]
            csv_reader = csv.DictReader(input_csv, fieldnames=headers)

            totals, transactions = bucket_transactions(csv_reader)
            output = {"totals": totals, "transactions": transactions}
    except IOError:
        logging.exception("Cannot read the input file")
        sys.exit()

    try:
        output_filename = f"{date.strftime('%Y-%m')}-output.json"
        with open(output_filename, 'w') as output_file:
            output_file.write(json.dumps(output, indent=2, sort_keys=True))
    except IOError:
        logging.exception("Cannot write the output file")
        sys.exit()

if __name__ == '__main__':
    main()
