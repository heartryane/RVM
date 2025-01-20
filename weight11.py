import os
import requests
from flask import Flask, request, jsonify
from threading import Thread
import base64
from tkinter import messagebox

# Flask app for handling callbacks
app = Flask(__name__)

# Xendit API Configuration
XENDIT_SECRET_KEY = os.getenv(
    "XENDIT_SECRET_KEY", "xnd_development_784ZEXK9AlW58ZU0G14xcX1riWoh9UbT1IMNu234woi3I9b7BPVZNpedKGoHkq"
)
X_CALLBACK_TOKEN = os.getenv("X_CALLBACK_TOKEN", "lWfixXJJo1y87WaLyL6G7rijl9VwYzQhmJ7lwYJsi0ldiP8f")
BASE_URL = "https://api.xendit.co"

# Function to create a one-time eWallet charge
def create_gcash_payment(reference_id, amount, success_url, failure_url):
    url = f"{BASE_URL}/payment_requests"
    encoded_api_key = base64.b64encode(f"{XENDIT_SECRET_KEY}:".encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "reference_id": reference_id,
        "amount": amount,
        "currency": "PHP",
        "country": "PH",
        "payment_method": {
            "type": "EWALLET",
            "ewallet": {
                "channel_code": "GCASH",
                "channel_properties": {
                    "success_return_url": success_url,
                    "failure_return_url": failure_url,  # Added this line
                },
            },
            "reusability": "ONE_TIME_USE",
        },
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print("Payment created successfully!")
        print(f"Redirect URL: {data['actions'][0]['url']}")
        return data["actions"][0]["url"]
    else:
        print("Error creating payment:", response.json())
        return None

# Webhook endpoint to handle payment callbacks
@app.route("/webhook", methods=["POST"])
def webhook():
    x_callback_token = request.headers.get("X-CALLBACK-TOKEN")
    if x_callback_token != X_CALLBACK_TOKEN:
        return jsonify({"error": "Invalid X-CALLBACK-TOKEN"}), 403

    webhook_data = request.json
    print("Webhook received:", webhook_data)

    event = webhook_data.get("event")
    if event == "payment_method.activated":
        data = webhook_data.get("data")
        print(f"Payment method activated: {data}")
    elif event == "ewallet.capture":
        data = webhook_data.get("data")
        print(f"Payment succeeded for Reference ID: {data.get('reference_id')}")
    else:
        print(f"Unhandled event: {event}")

    return jsonify({"message": "Webhook processed successfully"}), 200

@app.route("/success", methods=["GET"])
def success():
    return "<h1>Payment Successful</h1><p>Thank you for your payment!</p>"

@app.route("/failure", methods=["GET"])
def failure():
    return "<h1>Payment Failed</h1><p>We’re sorry, but your payment could not be processed.</p>"


# Main function to trigger payment and simulate callback
def main():
    # User Input
    reference_id = input("Enter Reference ID: ")
    amount = float(input("Enter Amount in PHP: "))
    success_url = "https://dced-103-107-81-10.ngrok-free.app/success"
    failure_url = "https://dced-103-107-81-10.ngrok-free.app/failure"

    # Create a GCash Payment
    payment_url = create_gcash_payment(reference_id, amount, success_url, failure_url)
    import os
    if os.name == "nt":  # Windows
        os.system(f"start {payment_url}")

    elif os.name == "posix":  # macOS/Linux
        os.system(f"open {payment_url}")

# Start Flask app in a separate thread
def run_flask():
    app.run(port=8080, debug=False)

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run the main payment flow
    main()
