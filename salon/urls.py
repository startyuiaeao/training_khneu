"""URL-маршрути додатку salon."""

from django.urls import path
from . import views

app_name = "salon"

urlpatterns = [
    # Dashboard
    path("", views.dashboard, name="dashboard"),
    # Клієнти
    path("clients/", views.client_list, name="client_list"),
    path("clients/add/", views.client_create, name="client_create"),
    path("clients/<int:pk>/", views.client_detail, name="client_detail"),
    path("clients/<int:pk>/edit/", views.client_edit, name="client_edit"),
    # Стрижки
    path("haircuts/", views.haircut_list, name="haircut_list"),
    path("haircuts/add/", views.haircut_create, name="haircut_create"),
    path("haircuts/<int:pk>/edit/", views.haircut_edit, name="haircut_edit"),
    # Філії
    path("branches/", views.branch_list, name="branch_list"),
    path("branches/add/", views.branch_create, name="branch_create"),
    path("branches/<int:pk>/edit/", views.branch_edit, name="branch_edit"),
    # Прайс-листи
    path("prices/", views.price_history, name="price_history"),
    path("prices/add/", views.pricelist_create, name="pricelist_create"),
    path("prices/<int:pk>/edit/", views.pricelist_edit, name="pricelist_edit"),
    path("prices/<int:pk>/archive/", views.pricelist_archive, name="pricelist_archive"),
    path(
        "prices/<int:pk>/add-haircut/",
        views.pricelist_add_haircut,
        name="pricelist_add_haircut",
    ),
    path(
        "prices/haircut/<int:pk>/edit/",
        views.pricelist_edit_haircut,
        name="pricelist_edit_haircut",
    ),
    path(
        "prices/haircut/<int:pk>/delete/",
        views.pricelist_delete_haircut,
        name="pricelist_delete_haircut",
    ),
    # Виконані роботи
    path("works/", views.work_list, name="work_list"),
    path("works/add/", views.work_create, name="work_create"),
    # Рахунок-фактура
    path("invoice/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    # Звіти
    path("reports/", views.report_general, name="report_general"),
    path("reports/branch/", views.report_branch, name="report_branch"),
]
