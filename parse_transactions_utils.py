import csv
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

    prompt = f"\nPick a category for ${row['Debit']} {row['Description']} (add '+' suffix to save):\n{category_options_string}\n\n"
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

def bucket_transactions(csv_reader, categories_blob, totals, transactions):
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

def bucket_transactions_across_files(month_csvs):
    categories_blob = read_categories()

    totals = {category: 0 for category in categories_blob["internalCategories"]}
    transactions = {category: [] for category in categories_blob["internalCategories"]}

    for month_csv in month_csvs:
        headers = [h.strip() for h in month_csv.readline().split(',')]
        csv_reader = csv.DictReader(month_csv, fieldnames=headers)
        bucket_transactions(csv_reader, categories_blob, totals, transactions)
    write_categories(categories_blob)

    return (totals, transactions)

