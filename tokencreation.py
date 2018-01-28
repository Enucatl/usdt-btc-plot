import click
import requests
import csv
import time
import json
import logging
import logging.config

from tokendistribution import check_transaction_link
from tokendistribution import recent_transactions
from log_config import log_config

logger = logging.getLogger(__name__)


@click.command()
@click.option("-v", "--verbose", count=True)
@click.argument("output", type=click.File("w"))
def main(verbose, output):
    logging.config.dictConfig(log_config(verbose))
    address = "3MbYQMMmSkC3AgWkj9FMo5LsPTW1zBTwXL"
    url = "http://omniexplorer.info/ask.aspx"
    min_transaction_timestamp = 0
    min_transaction_size = 0
    transactions = recent_transactions(
        address,
        min_transaction_timestamp,
        min_transaction_size)
    print(len(transactions), "transactions")
    writer = csv.writer(output)
    writer.writerow(["blocktime", "amount"])
    for t in transactions:
        if (t["type"] == "Grant Tokens"
            and t["valid"]
            and t["token"] == "TetherUS (#31)"):
                writer.writerow([t["blocktime"], t["amount"]])


if __name__ == "__main__":
    main()
