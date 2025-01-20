from flask import Flask, request, jsonify

app = Flask(__name__)

# Xendit callback token for validation
X_CALLBACK_TOKEN = "lWfixXJJo1y87WaLyL6G7rijl9VwYzQhmJ7lwYJsi0ldiP8f"  # Replace with your Xendit token

@app.route("/webhook", methods=["POST"])
def webhook():
    # Validate the X-Callback-Token header
    x_callback_token = request.headers.get("x-callback-token")
    if x_callback_token != X_CALLBACK_TOKEN:
        return jsonify({"error": "Invalid X-Callback-Token"}), 403

    # Process the incoming webhook data
    webhook_data = request.json
    print("Webhook received:", webhook_data)

    # Example: Handle payment success
    if webhook_data.get("event") == "payment.succeeded":
        payment_id = webhook_data["data"]["id"]
        reference_id = webhook_data["data"]["reference_id"]
        print(f"Payment succeeded: Payment ID {payment_id}, Reference ID {reference_id}")

    # Acknowledge receipt of the webhook
    return jsonify({"message": "Webhook processed successfully"}), 200

if __name__ == "__main__":
    app.run(port=8080)
