from flask import Request, render_template_string
from google.cloud import firestore
from firebase_admin import firestore
from google.cloud import monitoring_v3
from google.cloud import pubsub_v1
from google.protobuf.timestamp_pb2 import Timestamp
from email.mime.text import MIMEText
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2 import service_account
import logging
import os
import time
import base64
import google.auth
#import functions_framework


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

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
SENDER_EMAIL = "zjurowska@student.agh.edu.pl" 

# Cloud Functions env

project_id = "gcp-student-project-480912"

project_name = f"projects/{project_id}"
topic_name = f"projects/{project_id}/topics/new-entries"


def get_db():
    return firestore.Client()


def get_monitoring_client():
    return monitoring_v3.MetricServiceClient()


def get_publisher():
    return pubsub_v1.PublisherClient()

def refresh_credentials(credentials):
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

def send_email(to, subject, body):
    token_info={
        "token": os.environ.get("ACCESS_TOKEN"),
        "refresh_token": os.environ.get("REFRESH_TOKEN"), 
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": os.environ.get("CLIENT_ID"),
        "client_secret": os.environ.get("CLIENT_SECRET")
    }

    credentials = Credentials(
        token=token_info['token'],
        refresh_token=token_info['refresh_token'],
        token_uri=token_info['token_uri'],
        client_id=token_info['client_id'],
        client_secret=token_info['client_secret']
    )

    refresh_credentials(credentials)
    
    service = build("gmail", "v1", credentials=credentials)

    message = MIMEText(body)
    message["to"] = 'zofia28.12.2001@gmail.com'
    message["from"] = 'zjurowska@student.agh.edu.pl'
    message["subject"] = subject

    raw_message = base64.urlsafe_b64encode(
        message.as_bytes()
    ).decode()

    message_body= {'raw':raw_message}

    try:
        service.users().messages().send(userId="me",body=message_body).execute()
    except Exception as e:
        logging.error(f"Mail error: {e}")

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

    logging.error("Metric created")


def publish_event(text):
    try:
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(project_id, "new-entries")
        future = publisher.publish(topic_path, text.encode("utf-8"))
        message_id = future.result(timeout=10)
        logging.error(f"Pub/Sub succesfull")

    except Exception as e:
        logging.error(f"Pub/Sub error: {e}")


def main(request: Request):
    path = request.path
    method = request.method

    if path == "/health":
        logging.error(f"wywołano /health")
        return ("ok", 200)

    db = get_db()

    if method == "POST":
        text = request.form.get("text")
        if text:
            db.collection("entries").add({"text": text})
            nb_docs = db.collection("entries").count().get()[0][0].value
            try:
                increment_custom_metric(nb_docs)
            except Exception as e:
                logging.warning(f"Metric error: {e}")
            try:
                publish_event(text)
            except Exception as e:
                logging.warning(f"PubSub error: {e}")
            try:
                if text=="mail":
                    send_email( to="zofia.stateczna@gmail.com", subject="Nowy wpis", body=f"Dodano nowy wpis:\n\n{text}")
            except Exception as e:
                logging.warning(f"Mail error: {e}")
                    

    items = [doc.to_dict() for doc in db.collection("entries").stream()]
    text=""
    return render_template_string(HTML, items=items)
