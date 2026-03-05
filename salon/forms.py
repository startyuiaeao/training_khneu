"""Django-форми для додатку salon."""

from django import forms
from django.utils import timezone
from .models import (
    Client,
    Haircut,
    Branch,
    PricelistHead,
    PricelistHeadHaircut,
)


class ClientForm(forms.ModelForm):
    """Форма реєстрації / редагування клієнта."""

    class Meta:
        model = Client
        fields = [
            "last_name",
            "first_name",
            "middle_name",
            "gender",
            "phone",
            "email",
            "birth_date",
        ]
        widgets = {
            "last_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Прізвище"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Ім'я"}
            ),
            "middle_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "По батькові"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+380XXXXXXXXX"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "email@example.com"}
            ),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class HaircutForm(forms.ModelForm):
    """Форма створення / редагування стрижки."""

    class Meta:
        model = Haircut
        fields = ["name", "gender", "description", "duration_time", "is_active"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Назва стрижки"}
            ),
            "gender": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Опис стрижки",
                }
            ),
            "duration_time": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "Тривалість (хв)"}
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class BranchForm(forms.ModelForm):
    """Форма створення / редагування філії."""

    class Meta:
        model = Branch
        fields = ["name", "address", "contact_phone"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Назва філії"}
            ),
            "address": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Адреса"}
            ),
            "contact_phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Телефон"}
            ),
        }


class PricelistHeadForm(forms.ModelForm):
    """Форма створення прайс-листа."""

    class Meta:
        model = PricelistHead
        fields = ["branch", "valid_from", "valid_to"]
        widgets = {
            "branch": forms.Select(attrs={"class": "form-select"}),
            "valid_from": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "valid_to": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
        }


class PricelistHeadHaircutForm(forms.ModelForm):
    """Форма додавання ціни стрижки до прайс-листа."""

    class Meta:
        model = PricelistHeadHaircut
        fields = ["haircut", "price"]
        widgets = {
            "haircut": forms.Select(attrs={"class": "form-select"}),
            "price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ціна (грн)",
                    "step": "0.01",
                }
            ),
        }


class CompletedWorkForm(forms.Form):
    """Форма фіксації виконаної роботи.
    Дата за замовчуванням — сьогодні, але можна змінити.
    Стрижки сортуються за статтю обраного клієнта.
    """

    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Клієнт",
    )
    haircut = forms.ModelChoiceField(
        queryset=Haircut.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Стрижка",
    )
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all(),
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Філія",
    )
    work_date = forms.DateField(
        label="Дата виконання",
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["work_date"].initial = timezone.now().date().isoformat()

    def sort_haircuts_for_client(self, client_id):
        """Сортує стрижки: спочатку стать клієнта, потім
        унісекс, потім інші."""
        try:
            client = Client.objects.select_related("gender").get(pk=client_id)
            client_gender = client.gender
            from django.db.models import Case, When, Value, IntegerField

            self.fields["haircut"].queryset = (
                Haircut.objects.filter(is_active=True)
                .select_related("gender")
                .annotate(
                    sort_priority=Case(
                        When(gender=client_gender, then=Value(0)),
                        When(gender__name="Унісекс", then=Value(1)),
                        default=Value(2),
                        output_field=IntegerField(),
                    )
                )
                .order_by("sort_priority", "name")
            )
        except Client.DoesNotExist:
            pass


class ReportFilterForm(forms.Form):
    """Форма фільтрації для ЗАГАЛЬНОГО звіту.
    Без вибору філії — звіт завжди по всіх філіях.
    """

    date_from = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Дата з",
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Дата по",
    )


class ReportBranchFilterForm(forms.Form):
    """Форма фільтрації для звіту ПО ФІЛІЯХ.
    Чекбокси для вибору однієї або кількох філій.
    """

    date_from = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Дата з",
    )
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Дата по",
    )
    branches = forms.ModelMultipleChoiceField(
        queryset=Branch.objects.all(),
        widget=forms.CheckboxSelectMultiple(
            attrs={
                "class": "form-check-input",
            }
        ),
        label="Філії",
        required=True,
        error_messages={
            "required": "Оберіть хоча б одну філію.",
        },
    )
