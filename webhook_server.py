from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "arkashine_webhook_secret")
STATUS_FILE = "payment_status.json"

# ---------------- HELPERS ----------------
def load_status():
    """Load payment statuses safely"""
    if not os.path.exists(STATUS_FILE):
        print("[DEBUG] STATUS_FILE missing, returning empty dict")
        return {}
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                print("[WARN] STATUS_FILE corrupted, resetting")
                return {}
            return data
    except Exception as e:
        print(f"[ERROR] Failed to load STATUS_FILE: {e}")
        return {}

def save_status(payment_id, data):
    """Save/update a payment status by payment_id"""
    all_status = load_status()
    all_status[payment_id] = data
    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(all_status, f, indent=2)
        print(f"[DEBUG] Status saved for {payment_id}")
    except Exception as e:
        print(f"[ERROR] Failed to save STATUS_FILE: {e}")

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

    print("\n[DEBUG] New webhook received")
    print("[DEBUG] Payload (raw bytes):", payload)
    print("[DEBUG] Signature header:", signature)

    if not signature:
        print("[ERROR] Missing signature")
        return jsonify({"error": "Missing signature"}), 400

    # ---------------- VERIFY SIGNATURE ----------------
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()  # HEX DIGEST
    print("[DEBUG] Expected signature (hexdigest):", expected)

    if not hmac.compare_digest(expected, signature):
        print("[ERROR] Invalid signature, webhook rejected")
        return jsonify({"error": "Invalid signature"}), 400

    # ---------------- PARSE EVENT ----------------
    try:
        event = request.get_json(force=True)
        print("[DEBUG] Event JSON:", json.dumps(event, indent=2))
    except Exception as e:
        print(f"[ERROR] Failed to parse JSON: {e}")
        return jsonify({"error": "Invalid JSON"}), 400

    # ---------------- HANDLE EVENTS ----------------
    event_type = event.get("event", "unknown_event")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id", f"unknown_{int(time.time())}")

    if event_type == "payment.captured":
        save_status(payment_id, {
            "state": "success",
            "payment_id": payment_id,
            "amount": payment_entity.get("amount"),
            "currency": payment_entity.get("currency")
        })
        print(f"[INFO] Payment captured: {payment_id}")

    elif event_type == "payment.failed":
        reason = payment_entity.get("error_description", "Cancelled")
        save_status(payment_id, {
            "state": "failed",
            "payment_id": payment_id,
            "reason": reason,
            "amount": payment_entity.get("amount"),
            "currency": payment_entity.get("currency")
        })
        print(f"[INFO] Payment failed: {payment_id} | Reason: {reason}")

    else:
        save_status(payment_id, {
            "state": "unknown",
            "payment_id": payment_id,
            "event_type": event_type
        })
        print(f"[INFO] Unhandled event type: {event_type}")

    return jsonify({"status": "processed"}), 200

# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    import time
    print("[INFO] Starting webhook server on port 10000")
    app.run(host="0.0.0.0", port=10000, debug=True)
