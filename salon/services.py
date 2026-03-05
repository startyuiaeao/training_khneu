"""
Бізнес-логіка перукарні.
- Розрахунок знижки
- Визначення ціни
- Оновлення статусу клієнта
- Генерація номера чека
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Max, Q

from .models import (
    ClientCategory,
    PricelistHeadHaircut,
    CompletedWork,
)


def get_current_price(haircut, branch):
    """Отримати поточну ціну стрижки для конкретної філії."""
    today = timezone.now().date()
    entry = (
        PricelistHeadHaircut.objects.filter(
            haircut=haircut,
            pricelist_head__branch=branch,
            pricelist_head__valid_from__lte=today,
        )
        .filter(
            Q(pricelist_head__valid_to__gte=today)
            | Q(pricelist_head__valid_to__isnull=True)
        )
        .order_by("-pricelist_head__valid_from")
        .first()
    )

    return entry.price if entry else None


def calculate_discount(client):
    """Повертає відсоток знижки для клієнта."""
    return client.category.discount_percent


def calculate_final_price(base_price, discount_percent):
    """Обчислити фінальну ціну з урахуванням знижки."""
    discount_amount = base_price * discount_percent / Decimal("100")
    final = base_price - discount_amount
    return final.quantize(Decimal("0.01"))


def update_client_category(client):
    """Оновити категорію клієнта після нового візиту."""
    categories = ClientCategory.objects.order_by("-min_visits")
    for cat in categories:
        if client.total_visits >= cat.min_visits:
            if client.category != cat:
                client.category = cat
                client.save(update_fields=["category"])
            return


def increment_client_visits(client):
    """Збільшити лічильник візитів та оновити категорію."""
    client.total_visits += 1
    client.save(update_fields=["total_visits"])
    update_client_category(client)


def generate_check_id():
    """Згенерувати наступний номер чека."""
    max_check = CompletedWork.objects.aggregate(max_id=Max("check_id"))["max_id"]
    return (max_check or 0) + 1


def create_completed_work(client, haircut, branch, work_date=None):
    """Створити запис про виконану роботу з повною бізнес-логікою."""
    if work_date is None:
        work_date = timezone.now().date()

    base_price = get_current_price(haircut, branch)
    if base_price is None:
        raise ValueError(
            f"Ціну для стрижки '{haircut.name}' у філії '{branch.name}' не знайдено."
        )

    increment_client_visits(client)

    discount = calculate_discount(client)
    final_price = calculate_final_price(base_price, discount)

    work = CompletedWork.objects.create(
        client=client,
        haircut=haircut,
        branch=branch,
        work_date=work_date,
        discount_percent=discount,
        final_price=final_price,
        check_id=generate_check_id(),
    )
    return work
