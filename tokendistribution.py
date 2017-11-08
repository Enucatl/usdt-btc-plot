import click
import requests
import csv
import time
import json
import logging
import logging.config


from log_config import log_config


logger = logging.getLogger(__name__)


@click.command()
@click.option("-v", "--verbose", count=True)
@click.argument("nodes", type=click.File("w"))
@click.argument("links", type=click.File("w"))
def main(verbose, nodes, links):
    logging.config.dictConfig(log_config(verbose))
    node_writer = csv.writer(nodes)
    node_writer.writerow([
        "address",
        "balance"
        ])
    link_writer = csv.writer(links)
    link_writer.writerow([
        "id",
        "source",
        "target",
        "amount",
    ])
    known_nodes = set()
    new_nodes = set(["3MbYQMMmSkC3AgWkj9FMo5LsPTW1zBTwXL"])
    while new_nodes:
        logger.debug("found %s new nodes", len(new_nodes))
        node = new_nodes.pop()
        url = "http://omniexplorer.info/ask.aspx"
        params = {
            "api": "getsenderhistory",
            "address": node,
        }
        response = requests.get(url, params=params).json()
        transactions = response["transactions"]
        params = {
            "api": "getbalance",
            "prop": 31,
            "address": node,
        }
        balance = requests.get(url, params=params).json()
        node_writer.writerow([node, balance])
        known_nodes.update([node])
        logger.debug("found %s transactions", len(transactions))
        for transaction in transactions:
            time.sleep(0.2)
            params = {
                "api": "gettx",
                "txid": transaction
            }
            response = requests.get(url, params=params)
            t = json.loads("{" + response.text + "}")
            logger.debug("transaction %s", t)
            # keep only last two batches of 25 + 20 MUSDT
            if t["blocktime"] < 1509742213:
                break
            txid = t["txid"]
            source = t["sendingaddress"]
            target = t["referenceaddress"]
            amount = t["amount"]
            link_writer.writerow([
                txid, source, target, amount
            ])
            if target not in known_nodes:
                new_nodes.update([target])


if __name__ == "__main__":
    main()
