from django.db import models
from django.utils import timezone
import uuid

class BaseManager(models.Manager):
    """Manager base con métodos comunes"""
    def active(self):
        return self.filter(is_active=True)
    
    def created_today(self):
        today = timezone.now().date()
        return self.filter(created_at__date=today)

class TimeStampedModel(models.Model):
    """Modelo base con campos de auditoría"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class SoftDeleteModel(models.Model):
    """Modelo base para eliminación suave"""
    is_active = models.BooleanField(default=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        abstract = True
    
    def soft_delete(self):
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_active = True
        self.deleted_at = None
        self.save()