import argparse
import datetime


def get_date_from_filename(filename):
    date_string = filename.split('/')[-1][:len('2020-01')]
    return datetime.datetime.strptime(date_string, '%Y-%m')

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
