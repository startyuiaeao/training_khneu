"""
Моделі бази даних перукарні.
Таблиці: Gender, ClientCategory, Branch, Haircut,
         PricelistHead, PricelistHeadHaircut, Client, CompletedWork
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal


class Gender(models.Model):
    """Стать (Чоловіча / Жіноча / Унісекс)."""

    name = models.CharField(max_length=10, unique=True, verbose_name="Назва статі")

    class Meta:
        db_table = "genders"
        verbose_name = "Стать"
        verbose_name_plural = "Статі"

    def __str__(self):
        return self.name


class ClientCategory(models.Model):
    """Категорія клієнта (Звичайний / Постійний)."""

    name = models.CharField(max_length=50, verbose_name="Назва категорії")
    min_visits = models.PositiveIntegerField(
        default=0, verbose_name="Мінімум відвідувань"
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        verbose_name="Знижка (%)",
    )

    class Meta:
        db_table = "client_categories"
        verbose_name = "Категорія клієнта"
        verbose_name_plural = "Категорії клієнтів"
        ordering = ["min_visits"]

    def __str__(self):
        return f"{self.name} (знижка {self.discount_percent}%)"


class Branch(models.Model):
    """Філія перукарні."""

    name = models.CharField(max_length=100, verbose_name="Назва філії")
    address = models.CharField(max_length=255, verbose_name="Адреса")
    contact_phone = models.CharField(max_length=20, verbose_name="Телефон")

    class Meta:
        db_table = "branches"
        verbose_name = "Філія"
        verbose_name_plural = "Філії"

    def __str__(self):
        return self.name


class Haircut(models.Model):
    """Вид стрижки (каталог послуг)."""

    name = models.CharField(max_length=100, verbose_name="Назва стрижки")
    gender = models.ForeignKey(
        Gender,
        on_delete=models.PROTECT,
        db_column="genders_gender_id",
        verbose_name="Стать",
    )
    description = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="Опис"
    )
    duration_time = models.PositiveIntegerField(
        blank=True, null=True, verbose_name="Тривалість (хв)"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        db_table = "haircuts"
        verbose_name = "Стрижка"
        verbose_name_plural = "Стрижки"

    def __str__(self):
        return f"{self.name} ({self.gender})"

    def get_current_price(self, branch=None):
        """Повертає поточну ціну стрижки для вказаної філії."""
        today = timezone.now().date()
        qs = PricelistHeadHaircut.objects.filter(
            haircut=self,
            pricelist_head__valid_from__lte=today,
        ).filter(
            models.Q(pricelist_head__valid_to__gte=today)
            | models.Q(pricelist_head__valid_to__isnull=True)
        )
        if branch:
            qs = qs.filter(pricelist_head__branch=branch)
        entry = qs.order_by("-pricelist_head__valid_from").first()
        return entry.price if entry else None


class PricelistHead(models.Model):
    """Заголовок прайс-листа (період дії + філія)."""

    valid_from = models.DateField(verbose_name="Діє з")
    valid_to = models.DateField(blank=True, null=True, verbose_name="Діє до")
    branch = models.ForeignKey(
        Branch,
        on_delete=models.CASCADE,
        db_column="branches_branch_id",
        verbose_name="Філія",
    )

    class Meta:
        db_table = "pricelist_head"
        verbose_name = "Прайс-лист"
        verbose_name_plural = "Прайс-листи"
        ordering = ["-valid_from"]

    def __str__(self):
        to_str = self.valid_to or "теперішній час"
        return f"Прайс {self.branch} ({self.valid_from} — {to_str})"

    @property
    def is_current(self):
        today = timezone.now().date()
        if self.valid_to:
            return self.valid_from <= today <= self.valid_to
        return self.valid_from <= today


class PricelistHeadHaircut(models.Model):
    """Ціна конкретної стрижки в конкретному прайс-листі."""

    pricelist_head = models.ForeignKey(
        PricelistHead,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Прайс-лист",
    )
    haircut = models.ForeignKey(
        Haircut,
        on_delete=models.CASCADE,
        db_column="haircuts_haircut_id",
        verbose_name="Стрижка",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Ціна (грн)",
    )

    class Meta:
        db_table = "pricelist_head_haircuts"
        verbose_name = "Ціна стрижки"
        verbose_name_plural = "Ціни стрижок"
        unique_together = ("pricelist_head", "haircut")

    def __str__(self):
        return f"{self.haircut.name} — {self.price} грн"


class Client(models.Model):
    """Клієнт перукарні."""

    last_name = models.CharField(max_length=100, verbose_name="Прізвище")
    first_name = models.CharField(max_length=100, verbose_name="Ім'я")
    middle_name = models.CharField(
        max_length=100, blank=True, null=True, verbose_name="По батькові"
    )
    gender = models.ForeignKey(
        Gender,
        on_delete=models.PROTECT,
        db_column="genders_gender_id",
        verbose_name="Стать",
    )
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    email = models.EmailField(
        max_length=100, blank=True, null=True, verbose_name="Email"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата народження")
    registered_at = models.DateField(
        default=timezone.now, verbose_name="Дата реєстрації"
    )
    total_visits = models.PositiveIntegerField(
        default=0, verbose_name="Кількість візитів"
    )
    category = models.ForeignKey(
        ClientCategory,
        on_delete=models.PROTECT,
        db_column="client_categories_category_id",
        verbose_name="Категорія",
    )

    class Meta:
        db_table = "clients"
        verbose_name = "Клієнт"
        verbose_name_plural = "Клієнти"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        mid = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.last_name} {self.first_name}{mid}"

    @property
    def full_name(self):
        mid = f" {self.middle_name}" if self.middle_name else ""
        return f"{self.last_name} {self.first_name}{mid}"

    @property
    def is_loyal(self):
        return self.total_visits >= 5

    @property
    def discount(self):
        return self.category.discount_percent


class CompletedWork(models.Model):
    """Виконана робота (облік наданих послуг)."""

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        db_column="clients_client_id",
        related_name="works",
        verbose_name="Клієнт",
    )
    haircut = models.ForeignKey(
        Haircut,
        on_delete=models.PROTECT,
        db_column="haircuts_haircut_id",
        verbose_name="Стрижка",
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        db_column="branches_branch_id",
        verbose_name="Філія",
    )
    work_date = models.DateField(default=timezone.now, verbose_name="Дата виконання")
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("100"))],
        verbose_name="Знижка (%)",
    )
    final_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Підсумкова вартість (грн)",
    )
    check_id = models.PositiveIntegerField(unique=True, verbose_name="Номер чека")

    class Meta:
        db_table = "completed_works"
        verbose_name = "Виконана робота"
        verbose_name_plural = "Виконані роботи"
        ordering = ["-work_date"]

    def __str__(self):
        return f"Чек #{self.check_id} — {self.client} — {self.haircut}"
