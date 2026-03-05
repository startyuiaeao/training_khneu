"""Реєстрація моделей в адмін-панелі Django."""

from django.contrib import admin
from .models import (
    Gender,
    ClientCategory,
    Branch,
    Haircut,
    PricelistHead,
    PricelistHeadHaircut,
    Client,
    CompletedWork,
)


@admin.register(Gender)
class GenderAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(ClientCategory)
class ClientCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "min_visits", "discount_percent")
    list_editable = ("min_visits", "discount_percent")


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "contact_phone")
    search_fields = ("name", "address")


@admin.register(Haircut)
class HaircutAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "gender", "duration_time", "is_active")
    list_filter = ("gender", "is_active")
    search_fields = ("name",)
    list_editable = ("is_active",)


class PricelistHeadHaircutInline(admin.TabularInline):
    model = PricelistHeadHaircut
    extra = 1
    min_num = 1


@admin.register(PricelistHead)
class PricelistHeadAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "valid_from", "valid_to", "is_current")
    list_filter = ("branch",)
    inlines = [PricelistHeadHaircutInline]

    def is_current(self, obj):
        return obj.is_current

    is_current.boolean = True
    is_current.short_description = "Поточний"


@admin.register(PricelistHeadHaircut)
class PricelistHeadHaircutAdmin(admin.ModelAdmin):
    list_display = ("id", "pricelist_head", "haircut", "price")
    list_filter = ("pricelist_head__branch", "haircut")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "last_name",
        "first_name",
        "middle_name",
        "gender",
        "phone",
        "total_visits",
        "category",
        "registered_at",
    )
    list_filter = ("gender", "category")
    search_fields = ("last_name", "first_name", "phone")
    readonly_fields = ("total_visits",)


@admin.register(CompletedWork)
class CompletedWorkAdmin(admin.ModelAdmin):
    list_display = (
        "check_id",
        "client",
        "haircut",
        "branch",
        "work_date",
        "final_price",
    )
    list_filter = ("branch", "work_date")
    search_fields = ("client__last_name", "client__first_name", "check_id")
    date_hierarchy = "work_date"
