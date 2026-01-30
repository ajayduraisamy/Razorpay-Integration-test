from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os
import base64

app = Flask(__name__)

# ---------------- CONFIG ----------------
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "arkashine_webhook_secret")
STATUS_FILE = "payment_status.json"

# ---------------- HELPER ----------------
def load_status():
    """Load current payment statuses from file"""
    if not os.path.exists(STATUS_FILE):
        return {}
    with open(STATUS_FILE, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_status(payment_id, data):
    """Save/update a payment status by payment_id"""
    all_status = load_status()
    all_status[payment_id] = data
    with open(STATUS_FILE, "w") as f:
        json.dump(all_status, f, indent=2)

# ---------------- ROUTES ----------------
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

    # ---------------- VERIFY SIGNATURE ----------------
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).digest()
    expected_b64 = base64.b64encode(expected).decode()

    if not hmac.compare_digest(expected_b64, signature):
        return jsonify({"error": "Invalid signature"}), 400

    # ---------------- PARSE EVENT ----------------
    try:
        event = request.json
        # Optional: log event for debugging
        print(json.dumps(event, indent=2))
    except Exception as e:
        return jsonify({"error": "Invalid JSON"}), 400

    event_type = event.get("event")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id", "unknown")

    # ---------------- HANDLE EVENTS ----------------
    if event_type == "payment.captured":
        save_status(payment_id, {
            "state": "success",
            "payment_id": payment_id,
            "amount": payment_entity.get("amount"),
            "currency": payment_entity.get("currency")
        })

    elif event_type == "payment.failed":
        reason = payment_entity.get("error_description", "Cancelled")
        save_status(payment_id, {
            "state": "failed",
            "payment_id": payment_id,
            "reason": reason,
            "amount": payment_entity.get("amount"),
            "currency": payment_entity.get("currency")
        })

    else:
        # Handle other events if needed
        save_status(payment_id, {
            "state": "unknown",
            "payment_id": payment_id,
            "event_type": event_type
        })

    return jsonify({"status": "processed"}), 200

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
