import click
import requests
import csv
import time
import json
import logging
import logging.config
import mechanicalsoup as ms
import re


from log_config import log_config


logger = logging.getLogger(__name__)
url = "http://omniexplorer.info/ask.aspx"
txid_re = re.compile("txid")


def check_transaction_link(tag):
    return (
        tag.name == "a"
        and tag.has_attr("href")
        and txid_re.search(tag["href"])
        and tag.find("img", src="assets/img/token31.png"))


def recent_transactions(
        address,
        min_transaction_timestamp,
        min_transaction_size):
    browser_url = "http://omnichest.info/lookupadd.aspx?address={}&page={}"
    browser = ms.StatefulBrowser()
    confirmed_transactions = []
    transactions_too_old = False
    page_number = 1
    transactions = True
    while (not transactions_too_old) and transactions:
        time.sleep(0.2)
        browser.open(browser_url.format(address, page_number))
        page = browser.get_current_page()
        transactions = page.find_all(check_transaction_link)
        logger.debug("found %s transactions", len(transactions))
        for transaction in transactions:
            time.sleep(0.2)
            txid = transaction["href"][len("lookuptx.aspx?txid="):]
            logger.debug("looking for transaction %s", txid)
            params = {
                "api": "gettx",
                "txid": txid
            }
            response = requests.get(url, params=params)
            try:
                logger.debug("transaction %s", response.text)
                t = json.loads("{" + response.text + "}")
            except json.decoder.JSONDecodeError:
                continue
            try:
                blocktime = t["blocktime"]
                txid = t["txid"]
                source = t["sendingaddress"]
                target = t["referenceaddress"]
                amount = float(t["amount"])
                valid = t["valid"]
            except KeyError:
                continue
            if blocktime < min_transaction_timestamp:
                transactions_too_old = True
                break
            if (source != address
                or amount < min_transaction_size
                or not valid):
                continue
            confirmed_transactions.append(t)
        page_number += 1
    return confirmed_transactions



@click.command()
@click.option("-v", "--verbose", count=True)
@click.argument("nodes", type=click.File("w"))
@click.argument("links", type=click.File("w"))
def main(verbose, nodes, links):
    current_node = 0
    min_transaction_size = 100000
    min_transaction_timestamp = 1509742213
    logging.config.dictConfig(log_config(verbose))
    node_writer = csv.writer(nodes)
    node_writer.writerow([
        "address",
        "balance"
    ])
    link_writer = csv.writer(links)
    link_writer.writerow([
        "id",
        "timestamp",
        "source",
        "target",
        "value",
    ])
    known_nodes = set()
    new_nodes = set(["3MbYQMMmSkC3AgWkj9FMo5LsPTW1zBTwXL"])
    while new_nodes:
        logger.debug("found %s new nodes", len(new_nodes))
        node = new_nodes.pop()
        params = {
            "api": "getbalance",
            "prop": 31,
            "address": node,
        }
        time.sleep(0.2)
        balance = requests.get(url, params=params).json()
        node_writer.writerow([node, balance])
        known_nodes.update([node])
        transactions = recent_transactions(
            node,
            min_transaction_timestamp,
            min_transaction_size)
        logger.debug("found %s transactions", len(transactions))
        for t in transactions:
            blocktime = t["blocktime"]
            txid = t["txid"]
            source = t["sendingaddress"]
            target = t["referenceaddress"]
            amount = float(t["amount"])
            link_writer.writerow([
                txid, blocktime, source, target, amount
            ])
            if target not in known_nodes:
                new_nodes.add(target)
        current_node += 1
        logger.debug("analized %s nodes", current_node)


if __name__ == "__main__":
    main()
