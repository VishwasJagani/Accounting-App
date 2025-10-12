from django.db import models


class BaseModel(models.Model):

    """
    Base model class with created_at and updated_at fields.

    This class provides common fields for tracking the creation and last
    modification timestamps of database records.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        """Meta definition for BaseModel."""

        abstract = True
