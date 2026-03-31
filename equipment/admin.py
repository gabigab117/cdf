from django.contrib import admin

from .models import Equipment, EquipmentLoan, LoanItem


class LoanItemInline(admin.TabularInline):
    model = LoanItem
    extra = 1


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity", "loaned_quantity", "available_quantity")
    search_fields = ("name",)


@admin.register(EquipmentLoan)
class EquipmentLoanAdmin(admin.ModelAdmin):
    list_display = ("borrower_name", "date", "total_items", "total_quantity")
    list_filter = ("date",)
    search_fields = ("borrower_name",)
    inlines = [LoanItemInline]
