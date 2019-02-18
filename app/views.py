import datetime
import json
import requests
from flask import render_template, redirect, request
from app import app


# el nodo que estará interactuando con la aplicación.
CONNECTED_NODE_ADDRESS = "http://127.0.0.1:8000"


posts = []


# obtener el chain de algún nodo del blockchain, analizar los datos y almacenarlos localmente.
def fetch_posts():

     get_chain_address = '{}/chain'.format(CONNECTED_NODE_ADDRESS)
     response = requests.get(get_chain_address)

     if response.status_code == 200:
        content = []
        chain = json.loads(response.content)
        for block in  chain['chain']:
            for tx in  block['transactions']:
                tx["index"] = block["index"]
                tx["hash"] = block["previous_hash"]
                content.append(tx)

        global posts
        posts = sorted(content, key = lambda k: k['timestamp'], reverse = True)


@app.route('/')
def index():
    fetch_posts()
    return render_template('index.html',
                            title = '¿Qué tal son tus profes? .com',
                            posts = posts,
                            node_address = CONNECTED_NODE_ADDRESS,
                            readable_time = timestamp_to_string)


# Punto de acceso para crear una nueva transacción.
@app.route('/submit', methods = ['POST'])
def submit_textarea():
    post_content = request.form['content']
    author = request.form['author']

    post_object = {
        'author' : author,
        'content' : post_content
        # añadir nombre del profesor
        # y calificación.
    }

    # enviar una nueva transacción.
    new_tx_address = '{}/new_transaction'.format(CONNECTED_NODE_ADDRESS)
    request.post(new_tx_address,
                json = post_object,
                headers = {'Content-type': 'application/json'})

    return redirect('/')


def timestamp_to_string(epoch_time):
    return datetime.datetime.fromtimestamp(epoch_time).strftime('%H:%M')
