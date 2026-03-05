"""Тести додатку salon (Моделі, Сервіси, Представлення)."""

from decimal import Decimal
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

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
from salon.services import (
    calculate_final_price,
    increment_client_visits,
    create_completed_work,
)


class BaseSalonTest(TestCase):
    """Базовий клас для налаштування тестових даних."""

    @classmethod
    def setUpTestData(cls):
        # Стать
        cls.gender_male = Gender.objects.create(name="Чоловіча")
        cls.gender_female = Gender.objects.create(name="Жіноча")

        # Категорії
        cls.cat_regular = ClientCategory.objects.create(
            name="Звичайний", min_visits=0, discount_percent=Decimal("0.00")
        )
        cls.cat_loyal = ClientCategory.objects.create(
            name="Постійний", min_visits=5, discount_percent=Decimal("5.00")
        )

        # Філія
        cls.branch = Branch.objects.create(
            name="Тестова Філія",
            address="вул. Тестова, 1",
            contact_phone="+380000000000",
        )

        # Стрижка
        cls.haircut = Haircut.objects.create(
            name="Тестова Стрижка",
            gender=cls.gender_male,
            description="Опис",
            duration_time=30,
            is_active=True,
        )

        # Клієнт
        cls.client_obj = Client.objects.create(
            last_name="Іванов",
            first_name="Іван",
            gender=cls.gender_male,
            phone="+380999999999",
            category=cls.cat_regular,
            total_visits=0,
        )

        # Прайс-лист (активний з минулого місяця)
        today = timezone.now().date()
        cls.pricelist = PricelistHead.objects.create(
            branch=cls.branch,
            valid_from=today - timedelta(days=30),
        )
        cls.price_item = PricelistHeadHaircut.objects.create(
            pricelist_head=cls.pricelist, haircut=cls.haircut, price=Decimal("200.00")
        )


class SalonModelsTest(BaseSalonTest):
    """Тестування моделей."""

    def test_client_properties(self):
        """Тестування властивостей (properties) моделі Client."""
        self.assertEqual(self.client_obj.full_name, "Іванов Іван")
        self.assertFalse(self.client_obj.is_loyal)
        self.assertEqual(self.client_obj.discount, Decimal("0.00"))

        # Перевірка лояльності при 5 візитах
        self.client_obj.total_visits = 5
        self.client_obj.save()
        self.assertTrue(self.client_obj.is_loyal)

    def test_haircut_get_current_price(self):
        """Тестування отримання актуальної ціни для стрижки."""
        price = self.haircut.get_current_price(branch=self.branch)
        self.assertEqual(price, Decimal("200.00"))

    def test_pricelist_is_current(self):
        """Тестування активності прайс-листа."""
        self.assertTrue(self.pricelist.is_current)

        # Прайс-лист з минулого
        old_pricelist = PricelistHead.objects.create(
            branch=self.branch,
            valid_from=timezone.now().date() - timedelta(days=60),
            valid_to=timezone.now().date() - timedelta(days=31),
        )
        self.assertFalse(old_pricelist.is_current)

    def test_string_representations(self):
        """Тестування рядкових представлень (__str__)."""
        self.assertEqual(str(self.gender_male), "Чоловіча")
        self.assertEqual(str(self.branch), "Тестова Філія")
        self.assertEqual(str(self.haircut), "Тестова Стрижка (Чоловіча)")
        self.assertIn("Іванов Іван", str(self.client_obj))


class SalonServicesTest(BaseSalonTest):
    """Тестування бізнес-логіки та сервісів."""

    def test_calculate_final_price(self):
        """Тест розрахунку фінальної ціни зі знижкою."""
        base_price = Decimal("200.00")
        discount = Decimal("10.00")  # 10%
        final_price = calculate_final_price(base_price, discount)
        self.assertEqual(final_price, Decimal("180.00"))

    def test_increment_client_visits_and_category_update(self):
        """Тест збільшення кількості візитів та оновлення категорії клієнта."""
        self.assertEqual(self.client_obj.total_visits, 0)
        self.assertEqual(self.client_obj.category, self.cat_regular)

        # Симулюємо 5 візитів
        for _ in range(5):
            increment_client_visits(self.client_obj)

        self.client_obj.refresh_from_db()
        self.assertEqual(self.client_obj.total_visits, 5)
        # Категорія мала оновитися на "Постійний" (у якої min_visits=5)
        self.assertEqual(self.client_obj.category, self.cat_loyal)

    def test_create_completed_work(self):
        """Тест повного циклу створення виконаної роботи."""
        work = create_completed_work(
            client=self.client_obj,
            haircut=self.haircut,
            branch=self.branch,
        )

        self.client_obj.refresh_from_db()

        # Перевіряємо, що робота створилася
        self.assertIsInstance(work, CompletedWork)
        self.assertEqual(
            work.final_price, Decimal("200.00")
        )  # Знижка 0% у звичайного клієнта

        # Перевіряємо, що візит зараховано
        self.assertEqual(self.client_obj.total_visits, 1)

    def test_create_completed_work_without_price(self):
        """Тест створення роботи для стрижки без ціни в даній філії (очікується помилка)."""
        new_haircut = Haircut.objects.create(name="Без ціни", gender=self.gender_male)
        with self.assertRaises(ValueError):
            create_completed_work(
                client=self.client_obj,
                haircut=new_haircut,
                branch=self.branch,
            )


class SalonViewsTest(BaseSalonTest):
    """Тестування представлень (Views)."""

    def test_dashboard_view(self):
        """Тест головної сторінки."""
        response = self.client.get(reverse("salon:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "salon/dashboard.html")
        self.assertIn("total_clients", response.context)

    def test_client_list_view(self):
        """Тест сторінки зі списком клієнтів."""
        response = self.client.get(reverse("salon:client_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "salon/clients/client_list.html")
        self.assertContains(response, self.client_obj.last_name)

    def test_client_create_view(self):
        """Тест успішного створення клієнта через форму."""
        data = {
            "last_name": "Петров",
            "first_name": "Петро",
            "gender": self.gender_male.id,
            "phone": "+380501234567",
            "email": "petrov@example.com",
        }
        response = self.client.post(reverse("salon:client_create"), data)
        self.assertRedirects(response, reverse("salon:client_list"))
        self.assertTrue(Client.objects.filter(last_name="Петров").exists())

    def test_haircut_list_view(self):
        """Тест каталогу стрижок."""
        response = self.client.get(reverse("salon:haircut_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.haircut.name)

    def test_work_create_get_request(self):
        """Тест відкриття форми додавання виконаної роботи."""
        response = self.client.get(reverse("salon:work_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "salon/works/work_form.html")

    def test_report_general_view(self):
        """Тест сторінки загального звіту."""
        response = self.client.get(reverse("salon:report_general"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "salon/reports/report_general.html")
