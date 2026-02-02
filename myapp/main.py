from flask import Flask, request, render_template_string
from google.cloud import firestore
from google.cloud import monitoring_v3
from google.cloud import pubsub_v1
import logging
import os
import time
from google.protobuf.timestamp_pb2 import Timestamp

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

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

# Cloud Run env
project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
project_name = f"projects/{project_id}"
topic_name = f"projects/{project_id}/topics/new-entries"


def get_db():
    return firestore.Client()


def get_monitoring_client():
    return monitoring_v3.MetricServiceClient()


def get_publisher():
    return pubsub_v1.PublisherClient()


def increment_custom_metric(value=1):
    client = get_monitoring_client()

    series = monitoring_v3.TimeSeries()
    series.metric.type = "custom.googleapis.com/new_entries_count"
    series.resource.type = "global"
    series.resource.labels["project_id"] = project_id

    now = time.time()
    seconds = int(now)
    nanos = int((now - seconds) * 10**9)

    interval = monitoring_v3.TimeInterval(
        end_time=Timestamp(seconds=seconds, nanos=nanos)
    )

    point = monitoring_v3.Point(
        interval=interval,
        value=monitoring_v3.TypedValue(int64_value=value),
    )

    series.points = [point]

    client.create_time_series(name=project_name, time_series=[series])


def publish_event(text):
    try:
        publisher = get_publisher()
        publisher.publish(topic_name, text.encode("utf-8"))
    except Exception as e:
        logging.error(f"Pub/Sub error: {e}")


@app.route("/health")
def health():
    return "ok", 200


@app.route("/", methods=["GET", "POST"])
def index():
    db = get_db()
    if request.method == "POST":
        text = request.form.get("text")
        if text:
            doc_ref = db.collection("entries").add({"text": text})
            try:
                increment_custom_metric(1)
            except Exception as e:
                print(f"Warning: metric update failed: {e}")
            try:
                publish_event(text)
            except Exception as e:
                print(f"Warning: publish event failed: {e}")

    items = [doc.to_dict() for doc in db.collection("entries").stream()]
    return render_template_string(HTML, items=items)

if __name__ == "__main__":
     app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))