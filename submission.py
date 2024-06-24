import argparse
import pandas as pd

from src.pdf import process_pdf


def main(filepath: str):
    encounters = process_pdf(filepath)
    df = pd.DataFrame(encounters)
    df.to_csv('data/output/results.csv', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path-to-case-pdf',
                        metavar='path',
                        type=str,
                        help='Path to local test case with which to run your code'
                        )
    args = parser.parse_args()
    main(args.path_to_case_pdf)
