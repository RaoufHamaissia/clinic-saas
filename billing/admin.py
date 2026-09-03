from django.contrib import admin
from .models import Subscription, VisitRecord, Invoice
# Register your models here.

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("clinic", "plan", "status", "trial_ends_at")
    list_filter = ("plan", "status")


@admin.register(VisitRecord)
class VisitRecordAdmin(admin.ModelAdmin):
    list_display = ("clinic", "appointment", "amount", "invoice", "created_at")
    list_filter = ("clinic",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("clinic", "plan", "period_start", "period_end", "amount_due", "status")
    list_filter = ("plan", "status")