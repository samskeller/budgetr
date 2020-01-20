#! /usr/bin/env python

import argparse
import csv
import datetime
import json
import matplotlib
matplotlib.use('TkAgg') # necessary for running via virtualenv on mac os x
import matplotlib.pyplot as plt
import numpy as np

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

def output_month_plot(month, averages, month_string):
    categories = averages.keys()
    monthly_amounts = [round(month[category]) for category in categories]
    average_amounts = [round(averages[category]) for category in categories]
    x = np.arange(len(categories))  # the label locations
    width = 0.35  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, monthly_amounts, width, label=month_string)
    rects2 = ax.bar(x + width/2, average_amounts, width, label='Average')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Amount ($)')
    ax.set_xlabel('Category')
    ax.set_title(f"Spending in {month_string} compared to average")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.legend()

    def autolabel(rects):
        """Attach a text label above each bar in *rects*, displaying its height."""
        for rect in rects:
            height = rect.get_height()
            ax.annotate('{}'.format(height),
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize="x-small")

    autolabel(rects1)
    autolabel(rects2)

    # Make room for x-axis labels
    plt.gcf().subplots_adjust(bottom=0.4)

    # Rotate category names so they don't overlap
    plt.xticks(rotation=90)

    # Make sure y-axis is high enough to accommodate tall bar labels
    tallest_bar = max(monthly_amounts + average_amounts)
    plt.ylim(0, tallest_bar + (tallest_bar / 10))

    plt.savefig(f"{month_string}.png")

def get_date_from_filename(filename):
    date_string = filename.split('/')[-1][:len('2020-01-01')]
    return datetime.datetime.strptime(date_string, '%Y-%m-%d')

class TransactionsFileType(argparse.FileType):
    def __init__(self, **kwargs):
        return super().__init__(**kwargs)

    def __repr__(self):
        return super().__repr__()

    def __call__(self, value):
        parsed_file = super().__call__(value)
        try:
            get_date_from_filename(parsed_file.name)
        except ValueError:
            raise argparse.ArgumentTypeError('Not a valid date')

        return parsed_file

def parse_args():
    parser = argparse.ArgumentParser(description="Create a budget")
    parser.add_argument("month_csv", help="Input CSV file with transactions for a month", type=TransactionsFileType())
    parser.add_argument("totals_file", help="Monthly budget totals", type=argparse.FileType('r+'))
    return parser.parse_args()

def main():
    parsed_args = parse_args()

    with parsed_args.month_csv as month_csv:
        date = get_date_from_filename(parsed_args.month_csv.name)
        headers = [h.strip() for h in parsed_args.month_csv.readline().split(',')]
        csv_reader = csv.DictReader(parsed_args.month_csv, fieldnames=headers)

        monthly_totals, transactions = bucket_transactions(csv_reader)

    month_string = date.strftime('%Y-%m')
    try:
        output_filename = f"{month_string}-output.json"
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

    output_month_plot(averages, monthly_totals, month_string)

if __name__ == '__main__':
    main()
