from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import os

app = Flask(__name__)

# ================= CONFIG =================
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "arkashine_webhook_secret")
STATUS_FILE = "payment_status.json"

# ================= HELPERS =================
def load_status():
    if not os.path.exists(STATUS_FILE):
        return {}
    try:
        with open(STATUS_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception as e:
        print("[ERROR] load_status:", e)
        return {}

def save_status(payment_id, data):
    if not payment_id:
        print("[WARN] Missing payment_id, skipping save")
        return

    all_status = load_status()

    # Do not overwrite final state
    if payment_id in all_status and all_status[payment_id]["state"] in ("success", "failed"):
        print(f"[SKIP] Final state already saved for {payment_id}")
        return

    all_status[payment_id] = data

    with open(STATUS_FILE, "w") as f:
        json.dump(all_status, f, indent=2)

    print(f"[SAVED] {payment_id} → {data['state']}")

# ================= ROUTES =================
@app.route("/")
def home():
    return "Webhook server running", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    print("\n========= WEBHOOK RECEIVED =========")
    print("[DEBUG] Signature:", signature)

    if not signature:
        return "Missing signature", 400

    expected = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    print("[DEBUG] Expected:", expected)

    if not hmac.compare_digest(expected, signature):
        print("[ERROR] Signature mismatch")
        return "Invalid signature", 400

    event = request.get_json(force=True)
    event_type = event.get("event")

    print("[DEBUG] Event:", event_type)

    # ================= PAYMENT LINK SUCCESS =================
    if event_type == "payment_link.paid":
        payment = event["payload"]["payment"]["entity"]
        payment_id = payment["id"]

        save_status(payment_id, {
            "state": "success",
            "payment_id": payment_id,
            "amount": payment.get("amount"),
            "currency": payment.get("currency")
        })

        print(f"[FINAL] PAYMENT SUCCESS → {payment_id}")

    # ================= PAYMENT FAILED =================
    elif event_type == "payment.failed":
        payment = event["payload"]["payment"]["entity"]
        payment_id = payment["id"]

        save_status(payment_id, {
            "state": "failed",
            "payment_id": payment_id,
            "reason": payment.get("error_reason"),
            "description": payment.get("error_description")
        })

        print(f"[FINAL] PAYMENT FAILED → {payment_id}")

    else:
        print("[IGNORED] Event:", event_type)

    return "OK", 200

# ================= RUN =================
if __name__ == "__main__":
    print("Webhook running on port 10000")
    app.run(host="0.0.0.0", port=10000, debug=True)
