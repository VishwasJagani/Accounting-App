from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def send_mail(data):
    otp_type = data.get("otp_type")
    subject = data.get("subject", "No Subject")
    recipient_list = [data.get("email")]
    # from_email = ("Accounting App", settings.DEFAULT_FROM_EMAIL)
    from_email = "Accounting App"
    otp_code = data.get("otp_code")

    # Default context

    if otp_type == "verify_email":
        context = {
            "OTP": otp_code
        }
        text_content = f"Your OTP code is: {otp_code}."
        html_content = render_to_string(data.get('template_name'), context)

    if otp_type == "password_reset":
        context = {
            "OTP": otp_code
        }
        text_content = f"Your password reset OTP code is: {otp_code}."
        html_content = render_to_string(data.get('template_name'), context)

    msg = EmailMultiAlternatives(
        subject, text_content, from_email, recipient_list)

    if html_content:
        msg.attach_alternative(html_content, "text/html")

    msg.send()
