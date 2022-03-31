# supercard-idor

A proof of concept for an IDOR/forced browsing vulnerability at supercard.ch.

It is possible to view other peoples receipts if only the receipt's barcode is
known, and also browse receipts without knowing a barcode beforehand. The only
limit to this browsing is how much traffic supercard.ch can handle.

## How to run

```
$ pipenv shell
$ python -m main
```

This starts a program that searches through possible barcodes to find a
receipt. If a receipt is found, it is written to `receipt.pdf`.

## Description of the vulnerability

supercard.ch has a service where they offer digital receipts at
https://www.supercard.ch/de/app-digitale-services/meine-einkaeufe.html.
The page displays a list of receipts tied to the user's supercard.

### IDOR

There's an [IDOR vulnerability](https://portswigger.net/web-security/access-control/idor). supercard.ch exposes a user's receipt
at an address of form `https://www.supercard.ch/bin/coop/kbk/kassenzettelpoc?barcode=9900340068530032200003601234&pdfType=receipt`.
The address contains only the barcode of the receipt and anyone knowing it can see the receipt. There's no other access control.
The receipt contains some private data such as last digits of a credit card and the supercard number.

### Forced Browsing

The barcode is not random and can be effectively searched. The barcode consists of the following parts:

```
PREFIX  TRANSACTION ID  DATE    TOTAL    SHOP ID
990     023 00693       250322  0013440  1955
990     024 03837       250322  0003835  1955
990     027 04866       260322  0002990  1955
990     006 01930       250322  0001440  1827
990     006 01746       240322  0001195  1827
```

Since transaction ID seems to be sequential, it is fairly easy to search for
transactions in a given shop. We only need to search over possible prices.
