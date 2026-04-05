"""Utility functions for OTP, SMS, and authentication."""

import os
import random
from datetime import datetime
import requests


def generate_otp():
    """Generate a 6-digit OTP."""
    return str(random.randint(100000, 999999))


def send_otp_sms(mobile, otp):
    """Send OTP via SMS using available service.
    
    Priority order:
    1. Twilio (if configured)
    2. Fast2SMS (if configured)
    3. Fallback: Log to file and console
    """
    success = False

    # Try Twilio first
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if account_sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"Your OTP is {otp}",
                from_=from_number,
                to=mobile,
            )
            print(f"✓ OTP sent via Twilio to {mobile}")
            success = True
        except Exception as e:
            print(f"✗ Twilio error for {mobile}: {str(e)}")

    # Try Fast2SMS if Twilio failed
    if not success:
        fast2sms_key = os.getenv("FAST2SMS_API_KEY")
        if fast2sms_key:
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                params = {
                    "authorization": fast2sms_key,
                    "message": f"Your OTP is {otp}",
                    "language": "english",
                    "route": "q",
                    "numbers": mobile
                }
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    print(f"✓ OTP sent via Fast2SMS to {mobile}")
                    success = True
                else:
                    print(f"✗ Fast2SMS API error: {response.status_code}")
            except Exception as e:
                print(f"✗ Fast2SMS error for {mobile}: {str(e)}")

def send_otp_sms(mobile, otp):
    """Send OTP via SMS using available service.

    Priority order:
    1. Twilio (if configured)
    2. Fast2SMS (if configured)
    3. Fallback: Log to file and console
    """
    success = False

    # Try Twilio first
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if account_sid and auth_token and from_number:
        try:
            from twilio.rest import Client
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=f"Your OTP is {otp}",
                from_=from_number,
                to=mobile,
            )
            print(f"✓ OTP sent via Twilio to {mobile}")
            success = True
        except Exception as e:
            print(f"✗ Twilio error for {mobile}: {str(e)}")

    # Try Fast2SMS if Twilio failed
    if not success:
        fast2sms_key = os.getenv("FAST2SMS_API_KEY")
        if fast2sms_key:
            try:
                url = "https://www.fast2sms.com/dev/bulkV2"
                params = {
                    "authorization": fast2sms_key,
                    "message": f"Your OTP is {otp}",
                    "language": "english",
                    "route": "q",
                    "numbers": mobile
                }
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:
                    print(f"✓ OTP sent via Fast2SMS to {mobile}")
                    success = True
                else:
                    print(f"✗ Fast2SMS API error: {response.status_code} - {response.text}")
            except Exception as e:
                print(f"✗ Fast2SMS error for {mobile}: {str(e)}")

    # Fallback: Log to file and console
    if not success:
        try:
            otp_log_file = "otp_log.txt"
            with open(otp_log_file, "a") as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] Mobile: {mobile}, OTP: {otp}\n")
            print(f"✓ OTP logged to {otp_log_file} for {mobile}: {otp}")
            print(f"⚠️  DEVELOPMENT MODE: Check {otp_log_file} for OTP")
        except Exception as e:
            print(f"✗ Failed to log OTP: {str(e)}")
            print(f"OTP for {mobile}: {otp}")
