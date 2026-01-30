from flask import Flask, request, jsonify
import hmac, hashlib, json, os

app = Flask(__name__)

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "arkashine_webhook_secret")
STATUS_FILE = "payment_status.json"

def save_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

@app.route("/")
def home():
    return "Webhook server running", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return jsonify({"status": "ok"}), 200

    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        return jsonify({"error": "Missing signature"}), 400

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return jsonify({"error": "Invalid signature"}), 400

    event = request.json
    event_type = event.get("event")

    if event_type == "payment.captured":
        pid = event["payload"]["payment"]["entity"]["id"]
        save_status({"state": "success", "payment_id": pid})

    elif event_type == "payment.failed":
        reason = event["payload"]["payment"]["entity"].get(
            "error_description", "Cancelled"
        )
        save_status({"state": "failed", "reason": reason})

    return jsonify({"status": "processed"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
