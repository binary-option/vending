import os 
import json
import requests

# import from the 21 Developer Library
from two1.lib.wallet import Wallet
from two1.lib.bitserv.flask import Payment

# import flask web microframework
from flask import Flask
from flask import request

# vending machine stuff
from orderbook import add_to_book, get_order_book, get_book_quote
import machine_app

app = machine_app.vending_machine()
payment = Payment(app, machine_app.wallet)

# fetch current bitcoin price
@app.route('/btc_quote')
def btc_quote():
    q = machine_app.get_quote()
    return '%.5f' % q

# fetch option price
@app.route('/quote')
def price_quote():
    q = get_quote()
    buy_price, sell_price = get_book_quote(q)
    return 'BTCUSD: %.5f  buy: %.5f, sell: %.5f' % (q, buy_price, sell_price)
    
# buy a bitcoin option - require payment at max price, return the change
@app.route('/buy')
@payment.required(machine_app.PAYMENT_REQ)
def purchase():
    # extract payout address from client address
    client_payout_addr = request.args.get('payout_address')
    # price movement: up or down
    action = request.args.get('action')

    usd_rate = machine_app.get_quote()

    # add to book
    if action == 'up':
        change = add_to_book(client_payout_addr, machine_app.PAYMENT_REQ, usd_rate, True)
    else:
        change = add_to_book(client_payout_addr, machine_app.PAYMENT_REQ, usd_rate, False)

    txid = machine_app.wallet.send_to(client_payout_addr, change)
    return "Paid %d. BTCUSD is currently %.5f and will go %s." % \
            (machine_app.PAYMENT_REQ - change, usd_rate, action)

@app.route('/show')
def show_book():
    book = get_order_book()
    return json.dumps(book.dump_all())

if __name__ == '__main__':
    app.run(host='0.0.0.0')