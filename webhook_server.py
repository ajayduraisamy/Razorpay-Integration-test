from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os

app = Flask(__name__)

#  CONFIG 
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "arkashine_webhook_secret")
STATUS_FILE = "payment_status.json"

#  HELPERS 
def load_status():
    if not os.path.exists(STATUS_FILE):
        print("[DEBUG] payment_status.json not found, creating new")
        return {}

    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            print("[WARN] Corrupted JSON, resetting")
            return {}
    except Exception as e:
        print("[ERROR] load_status:", e)
        return {}

def save_status(payment_id, data):
    if not payment_id:
        print("[WARN] payment_id missing, skip save")
        return

    all_status = load_status()

    #  Do not overwrite FINAL state
    old = all_status.get(payment_id)
    if old and old.get("state") in ("success", "failed"):
        print(f"[SKIP] Final state already exists for {payment_id}")
        return

    all_status[payment_id] = data

    try:
        with open(STATUS_FILE, "w") as f:
            json.dump(all_status, f, indent=2)
        print(f"[DEBUG] Status saved → {payment_id}")
    except Exception as e:
        print("[ERROR] save_status:", e)

#  ROUTES 
@app.route("/")
def home():
    return "Razorpay Webhook Server Running", 200

@app.route("/webhook", methods=["POST", "GET"])
def webhook():

    if request.method == "GET":
        return jsonify({"status": "alive"}), 200

    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    print("\n================ NEW WEBHOOK ================")
    print("[DEBUG] Raw payload:", payload)
    print("[DEBUG] Signature:", signature)

    if not signature:
        return jsonify({"error": "Missing signature"}), 400

    #  VERIFY SIGNATURE 
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    print("[DEBUG] Expected signature:", expected_signature)

    if not hmac.compare_digest(expected_signature, signature):
        print("[ERROR] Signature mismatch")
        return jsonify({"error": "Invalid signature"}), 400

    #  PARSE JSON 
    try:
        event = request.get_json(force=True)
        print("[DEBUG] Event JSON:\n", json.dumps(event, indent=2))
    except Exception as e:
        print("[ERROR] JSON parse failed:", e)
        return jsonify({"error": "Invalid JSON"}), 400

    #  EVENT HANDLING 
    event_type = event.get("event")
    payment_entity = event.get("payload", {}).get("payment", {}).get("entity", {})
    payment_id = payment_entity.get("id")

    print("[DEBUG] Event type:", event_type)
    print("[DEBUG] Payment ID:", payment_id)

    #  SUCCESS
    if event_type == "payment.captured":
        save_status(payment_id, {
            "state": "success",
            "payment_id": payment_id,
            "amount": payment_entity.get("amount"),
            "currency": payment_entity.get("currency")
        })
        print(f"[FINAL] PAYMENT SUCCESS → {payment_id}")

    #  FAILED
    elif event_type == "payment.failed":
        reason = payment_entity.get("error_reason", "payment_failed")
        desc = payment_entity.get("error_description", "Customer cancelled or timeout")

        save_status(payment_id, {
            "state": "failed",
            "payment_id": payment_id,
            "reason": reason,
            "description": desc
        })
        print(f"[FINAL] PAYMENT FAILED → {payment_id} | {reason}")

    #  IGNORE EVERYTHING ELSE
    else:
        print(f"[IGNORED] Event ignored → {event_type}")

    return jsonify({"status": "processed"}), 200


if __name__ == "__main__":
    print("Starting Flask server on port 10000")
    app.run(host="0.0.0.0", port=10000, debug=True)
