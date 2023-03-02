
from flask import Flask
from threading import Thread


app = Flask('')

@app.route('/')
def home():
  return "Я жив"

def run():
  app.run(host='0.0.0.0', port=80)

def живем():
  t = Thread(target=run)
  t.start()
