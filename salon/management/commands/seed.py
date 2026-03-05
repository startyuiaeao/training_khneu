"""
Management command для заповнення БД тестовими даними.
Запуск: python manage.py seed
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta

from salon.models import (
    Gender,
    ClientCategory,
    Branch,
    Haircut,
    PricelistHead,
    PricelistHeadHaircut,
    Client,
    CompletedWork,
)
from salon.services import create_completed_work


class Command(BaseCommand):
    help = "Заповнює базу даних тестовими даними перукарні"

    def handle(self, *args, **options):
        self.stdout.write("\n🌱 Початок заповнення БД...\n")

        # ─── Статі ───
        g_male, _ = Gender.objects.get_or_create(name="Чоловіча")
        g_female, _ = Gender.objects.get_or_create(name="Жіноча")
        g_unisex, _ = Gender.objects.get_or_create(name="Унісекс")
        self.stdout.write("  ✅ Статі створено")

        # ─── Категорії клієнтів ───
        cat_regular, _ = ClientCategory.objects.get_or_create(
            name="Звичайний",
            defaults={"min_visits": 0, "discount_percent": Decimal("0.00")},
        )
        cat_loyal, _ = ClientCategory.objects.get_or_create(
            name="Постійний",
            defaults={"min_visits": 5, "discount_percent": Decimal("3.00")},
        )
        self.stdout.write("  ✅ Категорії клієнтів створено")

        # ─── Філії ───
        branch1, _ = Branch.objects.get_or_create(
            name="Центральна",
            defaults={
                "address": "вул. Хрещатик, 1, Київ",
                "contact_phone": "+380441234567",
            },
        )
        branch2, _ = Branch.objects.get_or_create(
            name="Подільська",
            defaults={
                "address": "вул. Сагайдачного, 15, Київ",
                "contact_phone": "+380441234568",
            },
        )
        self.stdout.write("  ✅ Філії створено")

        # ─── Стрижки ───
        haircuts_data = [
            ("Класична чоловіча", g_male, "Традиційна коротка стрижка", 30),
            ("Фейд", g_male, "Плавний перехід від короткого до довгого", 45),
            ("Каре", g_female, "Стрижка до плечей з рівним зрізом", 40),
            ("Піксі", g_female, "Коротка жіноча стрижка", 35),
            ("Боб", g_female, "Подовжене каре з градуюванням", 45),
            ("Дитяча стрижка", g_unisex, "Стрижка для дітей до 12 років", 20),
            ("Модельна чоловіча", g_male, "Креативна чоловіча стрижка", 50),
        ]
        haircuts = []
        for name, gender, desc, dur in haircuts_data:
            h, _ = Haircut.objects.get_or_create(
                name=name,
                defaults={
                    "gender": gender,
                    "description": desc,
                    "duration_time": dur,
                },
            )
            haircuts.append(h)
        self.stdout.write(f"  ✅ Стрижок створено: {len(haircuts)}")

        # ─── Прайс-листи ───
        today = timezone.now().date()
        for branch in [branch1, branch2]:
            old_pl, _ = PricelistHead.objects.get_or_create(
                branch=branch,
                valid_from=today - timedelta(days=90),
                defaults={"valid_to": today - timedelta(days=31)},
            )
            cur_pl, _ = PricelistHead.objects.get_or_create(
                branch=branch,
                valid_from=today - timedelta(days=30),
                defaults={"valid_to": None},
            )
            prices = [250, 350, 400, 300, 450, 150, 500]
            for i, h in enumerate(haircuts):
                PricelistHeadHaircut.objects.get_or_create(
                    pricelist_head=old_pl,
                    haircut=h,
                    defaults={"price": Decimal(str(prices[i] - 50))},
                )
                PricelistHeadHaircut.objects.get_or_create(
                    pricelist_head=cur_pl,
                    haircut=h,
                    defaults={"price": Decimal(str(prices[i]))},
                )
        self.stdout.write("  ✅ Прайс-листи створено")

        # ─── Клієнти ───
        clients_data = [
            ("Шевченко", "Тарас", "Григорович", g_male, "+380501111111"),
            ("Косач", "Леся", "Петрівна", g_female, "+380502222222"),
            ("Франко", "Іван", "Якович", g_male, "+380503333333"),
            ("Українка", "Леся", None, g_female, "+380504444444"),
            ("Сковорода", "Григорій", "Савич", g_male, "+380505555555"),
        ]
        clients = []
        for ln, fn, mn, gender, phone in clients_data:
            c, _ = Client.objects.get_or_create(
                last_name=ln,
                first_name=fn,
                defaults={
                    "middle_name": mn,
                    "gender": gender,
                    "phone": phone,
                    "category": cat_regular,
                    "registered_at": today - timedelta(days=60),
                },
            )
            clients.append(c)
        self.stdout.write(f"  ✅ Клієнтів створено: {len(clients)}")

        # ─── Виконані роботи ───
        if CompletedWork.objects.count() == 0:
            work_entries = [
                (clients[0], haircuts[0], branch1, today - timedelta(days=50)),
                (clients[0], haircuts[1], branch1, today - timedelta(days=40)),
                (clients[0], haircuts[0], branch1, today - timedelta(days=30)),
                (clients[0], haircuts[6], branch1, today - timedelta(days=20)),
                (clients[0], haircuts[0], branch1, today - timedelta(days=10)),
                (clients[0], haircuts[1], branch2, today - timedelta(days=3)),
                (clients[1], haircuts[2], branch1, today - timedelta(days=45)),
                (clients[1], haircuts[3], branch2, today - timedelta(days=15)),
                (clients[2], haircuts[0], branch2, today - timedelta(days=25)),
                (clients[3], haircuts[4], branch1, today - timedelta(days=5)),
            ]
            for client, haircut, branch, w_date in work_entries:
                try:
                    create_completed_work(client, haircut, branch, w_date)
                except ValueError as e:
                    self.stdout.write(f"  ⚠️  {e}")

            self.stdout.write(f"  ✅ Виконаних робіт: {CompletedWork.objects.count()}")

        self.stdout.write(self.style.SUCCESS("\n🎉 База даних успішно заповнена!\n"))
