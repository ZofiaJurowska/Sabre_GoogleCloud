from flask import Flask, request, render_template_string
from google.cloud import firestore
import logging
from google.cloud import monitoring_v3
import time
from google.protobuf.timestamp_pb2 import Timestamp


app = Flask(__name__)
db = firestore.Client()

HTML = """
<h2>Dodaj wpis</h2>
<form method="POST">
  <input name="text" placeholder="Wpisz tekst">
  <button type="submit">Dodaj</button>
</form>

<h2>Lista wpisów:</h2>
<ul>
{% for item in items %}
<li>{{ item['text'] }}</li>
{% endfor %}
</ul>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        text = request.form.get("text")
        db.collection("entries").add({"text": text})
    items = [doc.to_dict() for doc in db.collection("entries").stream()]
    return render_template_string(HTML, items=items)

if __name__ == "__main__":
    app.run()
