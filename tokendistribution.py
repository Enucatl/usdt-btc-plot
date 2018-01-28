import click
import requests
import csv
import time
import json
import logging
import logging.config
import mechanicalsoup as ms
import re
from datetime import datetime


from log_config import log_config


logger = logging.getLogger(__name__)
url = "http://omniexplorer.info/ask.aspx"
txid_re = re.compile("txid")


def find_table_field(string):
    def f(tag):
        result = (
            tag.name == "td"
            and tag.string == string)
        return result
    return f


def check_transaction_link(tag):
    result = (
        tag.name == "a"
        and tag.has_attr("href")
        and txid_re.search(tag["href"])
        and tag.find("img", src="assets/img/token31.png"))
    return result


def recent_transactions(
        address,
        min_transaction_timestamp,
        min_transaction_size):
    address_url = "http://omnichest.info/lookupadd.aspx?address={}&page={}"
    transaction_url = "https://omniexplorer.info/lookuptx.aspx?txid={}"
    browser = ms.StatefulBrowser()
    confirmed_transactions = []
    transactions_too_old = False
    page_number = 1
    transactions = True
    while (not transactions_too_old) and transactions:
        browser.open(address_url.format(address, page_number))
        page = browser.get_current_page()
        transactions = page.find_all(check_transaction_link)
        prices = [tag.parent.parent.parent.parent.find_next_sibling().h4.string
                  for tag in transactions]
        prices = [float(p)
                  for p in prices
                  if p != "N/A"
                 ]
        transactions = [transactions[i]
                        for i, p in enumerate(prices)
                        if i == len(prices) - 1 or p > min_transaction_size]
        logger.debug("found %s transactions", len(transactions))
        logger.debug("found %s large transactions", len(transactions))
        for transaction in transactions:
            txid = transaction["href"][len("lookuptx.aspx?txid="):]
            logger.debug("looking for transaction %s", txid)
            browser.open(transaction_url.format(txid))
            page = browser.get_current_page()
            datetime_text = page.find("span", id="ldatetime").string
            datetime_format = "%m/%d/%Y %I:%M:%S %p"
            blocktime = int((
                datetime.strptime(datetime_text, datetime_format) -
                datetime(1970, 1, 1)
            ).total_seconds())
            try:
                amount = float(page.find("span", id="lamount").string)
            except ValueError:
                amount = 0
            valid = page.find(string="CONFIRMED") == "CONFIRMED"
            source = page.find(find_table_field("Sender")).find_next_sibling().a.string
            try:
                target = page.find(find_table_field("Recipient")).find_next_sibling().a.string
            except AttributeError:
                target = ""
            token = page.find(find_table_field("Token")).find_next_sibling().a.string
            t_type = page.find("h4").text.replace(txid, "")
            t = {
                "txid": txid,
                "source": source,
                "target": target,
                "amount": amount,
                "blocktime": blocktime,
                "token": token,
                "type": t_type,
                "valid": valid,
            }
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
@click.option("--threshold", type=int, default=100000)
def main(verbose, nodes, links, threshold):
    current_node = 0
    min_transaction_size = threshold
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
        logger.info("found %s new nodes", len(new_nodes))
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
        logger.info("analized %s nodes", current_node)


if __name__ == "__main__":
    main()
