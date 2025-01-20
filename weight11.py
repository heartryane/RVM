import os
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for
from dotenv import load_dotenv
import hmac
import time
import base64

# Load environment variables
load_dotenv()
XENDIT_SECRET_KEY = os.getenv("XENDIT_SECRET_KEY")
X_CALLBACK_TOKEN = os.getenv("X_CALLBACK_TOKEN")

# Validate environment variables
if not XENDIT_SECRET_KEY or not X_CALLBACK_TOKEN:
    raise EnvironmentError("Missing XENDIT_SECRET_KEY or X_CALLBACK_TOKEN.")

BASE_URL = "https://api.xendit.co"

app = Flask(__name__)

# Root route with a user-friendly form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        # Process form submission
        amount = request.form.get("amount")
        success_url = url_for("success", _external=True)
        failure_url = url_for("failure", _external=True)

        # Generate a payment
        reference_id = f"rvm_{int(time.time())}"
        payment_url = create_gcash_payment(reference_id, float(amount), success_url, failure_url)

        if payment_url:
            return redirect(payment_url)  # Redirect user to GCash payment page
        else:
            return "<h1>Error creating payment. Please try again.</h1>", 500

    # Render the form for user input
    return '''
    <h1>Welcome to the RVM Payment Gateway</h1>
    <form method="POST">
        <label for="amount">Enter Amount (PHP):</label><br>
        <input type="number" id="amount" name="amount" required><br><br>
        <button type="submit">Pay with GCash</button>
    </form>
    '''

# Webhook endpoint for handling Xendit callbacks
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

# Function to create a GCash payment request
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
        print(f"Redirect URL: {data['actions'][0]['url']}")
        return data["actions"][0]["url"]
    else:
        print("Error creating payment:", response.json())
        return None

# Start the Flask server for Render
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
