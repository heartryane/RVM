"""import os
import requests
from flask import Flask, request, jsonify
import base64
from dotenv import load_dotenv
import hmac
import hashlib
import time
import weight

# Load environment variables
load_dotenv()
XENDIT_SECRET_KEY = os.getenv("XENDIT_SECRET_KEY")
X_CALLBACK_TOKEN = os.getenv("X_CALLBACK_TOKEN")

# Validate environment variables
if not XENDIT_SECRET_KEY or not X_CALLBACK_TOKEN:
    raise EnvironmentError("Missing XENDIT_SECRET_KEY or X_CALLBACK_TOKEN.")

BASE_URL = "https://api.xendit.co"

app = Flask(__name__)

# Root route for status checking
@app.route("/", methods=["GET"])
def home():
    return "<h1>Welcome to the RVM Payment Gateway</h1><p>Use the provided routes for payment processing.</p>"

# Webhook endpoint for handling Xendit callbacks
@app.route("/webhook", methods=["POST"])
def webhook():
    x_callback_token = request.headers.get("X-CALLBACK-TOKEN")
    if not hmac.compare_digest(x_callback_token, X_CALLBACK_TOKEN):
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

# Success page route
@app.route("/success", methods=["GET"])
def success():
    return "<h1>Payment Successful</h1><p>Thank you for your payment!</p>"

# Failure page route
@app.route("/failure", methods=["GET"])
def failure():
    return "<h1>Payment Failed</h1><p>We’re sorry, but your payment could not be processed.</p>"

# Route to create a GCash payment
@app.route("/create-payment", methods=["POST"])
def create_payment():
    try:
        data = request.json
        reference_id = f"rvm_{int(time.time())}"
        amount = data["amount"]
        success_url = data["success_url"]
        failure_url = data["failure_url"]

        payment_url = create_gcash_payment(reference_id, amount, success_url, failure_url)
        if payment_url:
            return jsonify({"payment_url": payment_url, "reference_id": reference_id}), 200
        else:
            return jsonify({"error": "Failed to create payment"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route to retrieve payment details
@app.route("/payment-details/<reference_id>", methods=["GET"])
def payment_details(reference_id):
    try:
        url = f"{BASE_URL}/payment_requests?reference_id={reference_id}"
        encoded_api_key = base64.b64encode(f"{XENDIT_SECRET_KEY}:".encode()).decode()
        headers = {"Authorization": f"Basic {encoded_api_key}"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json()}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Route to list all payments
@app.route("/list-payments", methods=["GET"])
def list_payments():
    try:
        url = f"{BASE_URL}/payment_requests"
        encoded_api_key = base64.b64encode(f"{XENDIT_SECRET_KEY}:".encode()).decode()
        headers = {"Authorization": f"Basic {encoded_api_key}"}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return jsonify(response.json()), 200
        else:
            return jsonify({"error": response.json()}), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# Function to create a GCash payment request
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
                    "failure_return_url": failure_url,
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

# Start the Flask server for Render
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
    """

import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import hmac
import time
import base64

# Load environment variables
load_dotenv()
XENDIT_SECRET_KEY = os.getenv("XENDIT_SECRET_KEY")
X_CALLBACK_TOKEN = os.getenv("X_CALLBACK_TOKEN")

BASE_URL = "https://api.xendit.co"

app = Flask(__name__)

# Root route with a user-friendly form
@app.route("/create-payment", methods=["POST"])
def create_payment():
    try:
        data = request.json
        reference_id = f"rvm_{int(time.time())}"
        amount = data["amount"]
        success_url = data["success_url"]
        failure_url = data["failure_url"]

        payment_url = create_gcash_payment(reference_id, amount, success_url, failure_url)
        if payment_url:
            return jsonify({"payment_url": payment_url, "reference_id": reference_id}), 200
        else:
            return jsonify({"error": "Failed to create payment"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/webhook", methods=["POST"])
def webhook():
    x_callback_token = request.headers.get("X-CALLBACK-TOKEN")
    if not hmac.compare_digest(x_callback_token, X_CALLBACK_TOKEN):
        return jsonify({"error": "Invalid X-CALLBACK-TOKEN"}), 403

    webhook_data = request.json
    print("Webhook received:", webhook_data)

    event = webhook_data.get("event")
    if event == "ewallet.capture":
        data = webhook_data.get("data")
        print(f"Payment succeeded for Reference ID: {data.get('reference_id')}")
        # Here you can add logic to update the transaction status in your database
    else:
        print(f"Unhandled event: {event}")

    return jsonify({"message": "Webhook processed successfully"}), 200

# Success page route
@app.route("/success", methods=["GET"])
def success():
    return "<h1>Payment Successful</h1><p>Thank you for your payment!</p>"

# Failure page route
@app.route("/failure", methods=["GET"])
def failure():
    return "<h1>Payment Failed</h1><p>We’re sorry, but your payment could not be processed.</p>"

def create_gcash_payment(reference_id, amount, success_url, failure_url):
    url = f"{BASE_URL}/payment_requests"
    headers = {
        "Authorization": f"Basic {base64.b64encode(f'{XENDIT_SECRET_KEY}:'.encode()).decode()}",
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
                    "failure_return_url": failure_url,
                },
            },
            "reusability": "ONE_TIME_USE",
        },
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 201:
        data = response.json()
        print("Payment created successfully!")
        return data["actions"][0]["url"]
    else:
        print("Error creating payment:", response.json())
        return None