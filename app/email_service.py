import os
import logging
import requests
from flask import current_app, url_for

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, html_content: str, text_content: str | None = None) -> bool:
    """
    Send transactional email via Resend API or Brevo API if configured.
    Falls back gracefully to logging in console/development.
    """
    resend_api_key = os.environ.get('RESEND_API_KEY')
    brevo_api_key = os.environ.get('BREVO_API_KEY')
    sender_email = os.environ.get('MAIL_SENDER', 'notifications@pallottibookloop.in')
    sender_name = os.environ.get('MAIL_SENDER_NAME', 'Pallotti BookLoop')

    # 1. Resend integration
    if resend_api_key:
        try:
            res = requests.post(
                'https://api.resend.com/emails',
                headers={
                    'Authorization': f'Bearer {resend_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'from': f'{sender_name} <{sender_email}>',
                    'to': [to_email],
                    'subject': subject,
                    'html': html_content,
                    'text': text_content or html_content,
                },
                timeout=8
            )
            if res.status_code in [200, 201, 202]:
                logger.info(f"Email sent via Resend to {to_email}: {subject}")
                return True
            else:
                logger.warning(f"Resend API error ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Failed to send email via Resend: {str(e)}")

    # 2. Brevo integration
    elif brevo_api_key:
        try:
            res = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': brevo_api_key,
                    'Content-Type': 'application/json',
                },
                json={
                    'sender': {'name': sender_name, 'email': sender_email},
                    'to': [{'email': to_email}],
                    'subject': subject,
                    'htmlContent': html_content,
                    'textContent': text_content or html_content,
                },
                timeout=8
            )
            if res.status_code in [200, 201, 202]:
                logger.info(f"Email sent via Brevo to {to_email}: {subject}")
                return True
            else:
                logger.warning(f"Brevo API error ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Failed to send email via Brevo: {str(e)}")

    # 3. Development / Test fallback
    logger.info(
        f"\n========== [EMAIL NOTIFICATION (DEV/CONSOLE FALLBACK)] ==========\n"
        f"To: {to_email}\n"
        f"Subject: {subject}\n"
        f"Body:\n{text_content or html_content}\n"
        f"=================================================================\n"
    )
    return True


def send_verification_email(user, token: str) -> bool:
    """Send account email confirmation link."""
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    subject = "Verify Your Pallotti BookLoop Account"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #0f2744;">Welcome to Pallotti BookLoop!</h2>
        <p>Hi {user.full_name},</p>
        <p>Thank you for joining the St. Vincent Pallotti College textbook exchange platform. Please verify your email to begin listing books and sending exchange requests.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{verify_url}" style="background-color: #0d9488; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Verify My Account</a>
        </div>
        <p style="color: #64748b; font-size: 13px;">This link will expire in 24 hours. If you did not sign up for Pallotti BookLoop, you can safely ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">Pallotti BookLoop &bull; SVPCET Student Academic Marketplace</p>
    </div>
    """
    text = f"Hi {user.full_name},\n\nPlease verify your Pallotti BookLoop account by visiting: {verify_url}\n\nLink expires in 24 hours."
    return send_email(user.college_email, subject, html, text)


def send_password_reset_email(user, token: str) -> bool:
    """Send single-use password reset link."""
    reset_url = url_for('auth.reset_password', token=token, _external=True)
    subject = "Reset Your Pallotti BookLoop Password"
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h2 style="color: #0f2744;">Password Reset Request</h2>
        <p>Hi {user.full_name},</p>
        <p>We received a request to reset your password for Pallotti BookLoop. Click the button below to set a new password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_url}" style="background-color: #0f2744; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Reset Password</a>
        </div>
        <p style="color: #64748b; font-size: 13px;">This link is valid for 1 hour and can only be used once. If you did not request this, your password remains secure.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">Pallotti BookLoop &bull; SVPCET Student Academic Marketplace</p>
    </div>
    """
    text = f"Hi {user.full_name},\n\nReset your password here: {reset_url}\n\nLink expires in 1 hour."
    return send_email(user.college_email, subject, html, text)


def send_exchange_notification(to_email: str, title: str, message: str, action_url: str | None = None) -> bool:
    """Send notification email regarding exchange status update."""
    action_html = f'<div style="margin: 20px 0;"><a href="{action_url}" style="background-color: #0d9488; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">View in Dashboard</a></div>' if action_url else ''
    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
        <h3 style="color: #0f2744;">{title}</h3>
        <p>{message}</p>
        {action_html}
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
        <p style="color: #94a3b8; font-size: 12px;">Pallotti BookLoop &bull; SVPCET Student Academic Marketplace</p>
    </div>
    """
    text = f"{title}\n\n{message}\n\n{action_url or ''}"
    return send_email(to_email, title, html, text)
