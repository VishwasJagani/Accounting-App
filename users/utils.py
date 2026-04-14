# Rest Framework
import os
import requests
from decimal import Decimal
from rest_framework_simplejwt.tokens import RefreshToken

# Django
from django.core.mail import send_mail


def is_required(value):
    return value in ["", None]


def get_user_token(user_instance):
    """
    Get the refresh and access tokens for the user.
    """
    if user_instance:
        refresh = RefreshToken.for_user(user_instance)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    return None


def is_valid_image(file):
    """
    Check if the uploaded file is a valid image.
    """
    try:
        extension = file.name.split('.')[-1]
        if extension.lower() not in ['jpg', 'jpeg', 'png']:
            return False

        return True

    except Exception as e:
        return False


def fetch_company_info_from_gst_number(gst_number):

    api_key = os.getenv("GST_API_KEY")
    api_url = f"https://sheet.gstincheck.co.in/check/{api_key}/{gst_number}"

    resp = requests.get(api_url)

    if resp.status_code == 200:
        return resp.json()

    return None


def update_bank_account_balance(obj):
    """
    Update the balance of a bank account based on the transaction.
    """
    from users import models as users_models

    if not obj:
        raise ValueError("Transaction object is required.")

    if not obj.bank:
        raise ValueError("Bank account is required for the transaction.")

    if not obj.amount or obj.amount <= 0:
        raise ValueError("Transaction amount must be a positive number.")

    try:
        bank = users_models.UserBankAccount.objects.get(
            id=obj.bank.id, is_deleted=False)
    except users_models.UserBankAccount.DoesNotExist:
        raise ValueError("Bank account not found or is deleted.")

    if obj.transaction_type == 'income':
        bank.current_balance = (
            bank.current_balance or Decimal('0.00')) + obj.amount
    elif obj.transaction_type in ['expense', 'transfer']:
        if bank.current_balance is None or bank.current_balance < obj.amount:
            raise ValueError("Insufficient balance in the bank account.")
        bank.current_balance = (
            bank.current_balance or Decimal('0.00')) - obj.amount
    
    bank.save()


def send_mail(data):
    """
    Send an email using the provided data.
    """
    # Implement email sending logic here
    pass
