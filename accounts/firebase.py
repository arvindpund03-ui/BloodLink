import json
import logging
import os

import firebase_admin
from firebase_admin import credentials, messaging

logger = logging.getLogger(__name__)


def initialize_firebase():
    if firebase_admin._apps:
        return firebase_admin.get_app()

    service_account_json = os.environ.get(
        "FIREBASE_SERVICE_ACCOUNT_JSON"
    )

    if not service_account_json:
        logger.error(
            "FIREBASE_SERVICE_ACCOUNT_JSON is not configured."
        )
        return None

    try:
        service_account_info = json.loads(
            service_account_json
        )

        cred = credentials.Certificate(
            service_account_info
        )

        return firebase_admin.initialize_app(cred)

    except Exception:
        logger.exception(
            "Firebase Admin SDK initialization failed."
        )
        return None


def send_admin_emergency_notification(emergency):
    app = initialize_firebase()

    if app is None:
        return False

    admin_token = os.environ.get(
        "FCM_ADMIN_TOKEN"
    )

    if not admin_token:
        logger.error(
            "FCM_ADMIN_TOKEN is not configured."
        )
        return False

    try:
        title = (
            f"🚨 BLOODLINK {emergency.urgency} EMERGENCY"
        )

        body = (
            f"{emergency.patient_name} needs "
            f"{emergency.units_required} unit(s) "
            f"{emergency.blood_group} blood "
            f"in {emergency.city}."
        )

        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),

            data={
                "type": "emergency",
                "emergency_id": str(emergency.id),
                "patient_name": emergency.patient_name,
                "blood_group": emergency.blood_group,
                "units_required": str(
                    emergency.units_required
                ),
                "hospital_name": emergency.hospital_name,
                "city": emergency.city,
                "contact_number": emergency.contact_number,
                "emergency_type": emergency.emergency_type,
                "urgency": emergency.urgency,
                "status": emergency.status,
            },

            token=admin_token,

            android=messaging.AndroidConfig(
                priority="high",

                notification=messaging.AndroidNotification(
                    channel_id="bloodlink_emergency",
                    sound="default",
                    priority="high",
                    default_sound=True,
                    default_vibrate_timings=True,
                ),
            ),
        )

        response = messaging.send(message)

        logger.info(
            "BloodLink emergency FCM sent successfully: %s",
            response,
        )

        return True

    except Exception:
        logger.exception(
            "Failed to send BloodLink emergency FCM."
        )
        return False