"""Views (подання) додатку salon."""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone

from .models import (
    Client,
    Haircut,
    Branch,
    ClientCategory,
    PricelistHead,
    PricelistHeadHaircut,
    CompletedWork,
)
from .forms import (
    ClientForm,
    HaircutForm,
    BranchForm,
    PricelistHeadForm,
    PricelistHeadHaircutForm,
    CompletedWorkForm,
    ReportFilterForm,
    ReportBranchFilterForm,
)
from .services import create_completed_work, get_current_price


# ──────────────── Dashboard ────────────────


def dashboard(request):
    context = {
        "total_clients": Client.objects.count(),
        "loyal_clients": Client.objects.filter(total_visits__gte=5).count(),
        "total_haircuts": Haircut.objects.filter(is_active=True).count(),
        "total_branches": Branch.objects.count(),
        "total_works": CompletedWork.objects.count(),
        "recent_works": CompletedWork.objects.select_related(
            "client", "haircut", "branch"
        )[:10],
    }
    return render(request, "salon/dashboard.html", context)


# ──────────────── Клієнти ──────────────────


def client_list(request):
    """Список клієнтів з пошуком.
    Case-insensitive: шукає як малими так і великими літерами.
    Для кирилиці в SQLite — додатково шукає варіанти регістру.
    """
    query = request.GET.get("q", "").strip()
    clients = Client.objects.select_related("gender", "category")
    if query:
        terms = query.split()
        q_filter = Q()
        for term in terms:
            t_low = term.lower()
            t_up = term.upper()
            t_title = term.title()
            q_filter &= (
                Q(last_name__icontains=term)
                | Q(first_name__icontains=term)
                | Q(middle_name__icontains=term)
                | Q(phone__icontains=term)
                | Q(email__icontains=term)
                | Q(last_name__contains=t_low)
                | Q(last_name__contains=t_up)
                | Q(last_name__contains=t_title)
                | Q(first_name__contains=t_low)
                | Q(first_name__contains=t_up)
                | Q(first_name__contains=t_title)
                | Q(middle_name__contains=t_low)
                | Q(middle_name__contains=t_up)
                | Q(middle_name__contains=t_title)
            )
        clients = clients.filter(q_filter).distinct()
    return render(
        request,
        "salon/clients/client_list.html",
        {
            "clients": clients,
            "query": query,
        },
    )


def client_create(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save(commit=False)
            default_cat = ClientCategory.objects.order_by("min_visits").first()
            client.category = default_cat
            client.registered_at = timezone.now().date()
            client.save()
            messages.success(request, f"Клієнта {client.full_name} зареєстровано!")
            return redirect("salon:client_list")
    else:
        form = ClientForm()
    return render(
        request,
        "salon/clients/client_form.html",
        {
            "form": form,
            "title": "Реєстрація клієнта",
        },
    )


def client_detail(request, pk):
    client = get_object_or_404(
        Client.objects.select_related("gender", "category"), pk=pk
    )
    works = client.works.select_related("haircut", "branch").order_by("-work_date")
    return render(
        request,
        "salon/clients/client_detail.html",
        {
            "client": client,
            "works": works,
        },
    )


def client_edit(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, "Дані клієнта оновлено!")
            return redirect("salon:client_detail", pk=client.pk)
    else:
        form = ClientForm(instance=client)
    return render(
        request,
        "salon/clients/client_form.html",
        {
            "form": form,
            "title": f"Редагування: {client.full_name}",
        },
    )


# ──────────────── Стрижки ─────────────────


def haircut_list(request):
    haircuts = Haircut.objects.select_related("gender").all()
    return render(
        request,
        "salon/haircuts/haircut_list.html",
        {
            "haircuts": haircuts,
        },
    )


def haircut_create(request):
    if request.method == "POST":
        form = HaircutForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Стрижку додано до каталогу!")
            return redirect("salon:haircut_list")
    else:
        form = HaircutForm()
    return render(
        request,
        "salon/haircuts/haircut_form.html",
        {
            "form": form,
            "title": "Нова стрижка",
        },
    )


def haircut_edit(request, pk):
    haircut = get_object_or_404(Haircut, pk=pk)
    if request.method == "POST":
        form = HaircutForm(request.POST, instance=haircut)
        if form.is_valid():
            form.save()
            messages.success(request, "Стрижку оновлено!")
            return redirect("salon:haircut_list")
    else:
        form = HaircutForm(instance=haircut)
    return render(
        request,
        "salon/haircuts/haircut_form.html",
        {
            "form": form,
            "title": f"Редагування: {haircut.name}",
        },
    )


# ──────────────── Філії ───────────────────


def branch_list(request):
    branches = Branch.objects.all()
    return render(
        request,
        "salon/branches/branch_list.html",
        {
            "branches": branches,
        },
    )


def branch_create(request):
    if request.method == "POST":
        form = BranchForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Філію додано!")
            return redirect("salon:branch_list")
    else:
        form = BranchForm()
    return render(
        request,
        "salon/branches/branch_form.html",
        {
            "form": form,
            "title": "Нова філія",
        },
    )


def branch_edit(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        form = BranchForm(request.POST, instance=branch)
        if form.is_valid():
            form.save()
            messages.success(request, "Філію оновлено!")
            return redirect("salon:branch_list")
    else:
        form = BranchForm(instance=branch)
    return render(
        request,
        "salon/branches/branch_form.html",
        {
            "form": form,
            "title": f"Редагування: {branch.name}",
        },
    )


# ──────────────── Прайс-листи ────────────


def price_history(request):
    pricelists = (
        PricelistHead.objects.select_related("branch")
        .prefetch_related("items__haircut")
        .all()
    )
    return render(
        request,
        "salon/prices/price_history.html",
        {
            "pricelists": pricelists,
        },
    )


def pricelist_create(request):
    if request.method == "POST":
        form = PricelistHeadForm(request.POST)
        if form.is_valid():
            pricelist = form.save()
            messages.success(request, "Прайс-лист створено! Додайте ціни на стрижки.")
            return redirect("salon:pricelist_add_haircut", pk=pricelist.pk)
    else:
        form = PricelistHeadForm()
    return render(
        request,
        "salon/prices/price_form.html",
        {
            "form": form,
            "title": "Новий прайс-лист",
        },
    )


def pricelist_edit(request, pk):
    pricelist = get_object_or_404(PricelistHead, pk=pk)
    if request.method == "POST":
        form = PricelistHeadForm(request.POST, instance=pricelist)
        if form.is_valid():
            form.save()
            messages.success(request, "Прайс-лист оновлено!")
            return redirect("salon:price_history")
    else:
        form = PricelistHeadForm(instance=pricelist)
    return render(
        request,
        "salon/prices/price_form.html",
        {
            "form": form,
            "title": f"Редагування: {pricelist}",
            "pricelist": pricelist,
            "items": pricelist.items.select_related("haircut").all(),
        },
    )


def pricelist_archive(request, pk):
    pricelist = get_object_or_404(PricelistHead, pk=pk)
    if request.method == "POST":
        from datetime import timedelta

        today = timezone.now().date()
        if pricelist.is_current or (
            pricelist.valid_to is None or pricelist.valid_to >= today
        ):
            pricelist.valid_to = today - timedelta(days=1)
            pricelist.save(update_fields=["valid_to"])
            messages.success(request, "Прайс-лист переміщено в архів.")
        else:
            messages.info(request, "Прайс-лист вже архівний.")
    return redirect("salon:price_history")


def pricelist_edit_haircut(request, pk):
    item = get_object_or_404(
        PricelistHeadHaircut.objects.select_related("pricelist_head"), pk=pk
    )
    if request.method == "POST":
        form = PricelistHeadHaircutForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Ціну оновлено!")
            return redirect("salon:pricelist_add_haircut", pk=item.pricelist_head.pk)
    else:
        form = PricelistHeadHaircutForm(instance=item)
    return render(
        request,
        "salon/prices/price_form.html",
        {
            "form": form,
            "title": f"Редагування ціни: {item.haircut.name}",
            "pricelist": item.pricelist_head,
            "items": item.pricelist_head.items.select_related("haircut").all(),
        },
    )


def pricelist_delete_haircut(request, pk):
    item = get_object_or_404(
        PricelistHeadHaircut.objects.select_related("pricelist_head"), pk=pk
    )
    pricelist_pk = item.pricelist_head.pk
    if request.method == "POST":
        item.delete()
        messages.success(request, "Ціну видалено!")
    return redirect("salon:pricelist_add_haircut", pk=pricelist_pk)


def pricelist_add_haircut(request, pk):
    pricelist = get_object_or_404(PricelistHead, pk=pk)
    if request.method == "POST":
        form = PricelistHeadHaircutForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.pricelist_head = pricelist
            item.save()
            messages.success(request, "Ціну додано!")
            return redirect("salon:pricelist_add_haircut", pk=pk)
    else:
        form = PricelistHeadHaircutForm()

    items = pricelist.items.select_related("haircut").all()
    return render(
        request,
        "salon/prices/price_form.html",
        {
            "form": form,
            "title": f"Додати ціни: {pricelist}",
            "pricelist": pricelist,
            "items": items,
        },
    )


# ──────────────── Виконані роботи ────────


def work_list(request):
    works = CompletedWork.objects.select_related(
        "client", "haircut", "branch"
    ).order_by("-work_date", "-pk")
    return render(
        request,
        "salon/works/work_list.html",
        {
            "works": works,
        },
    )


def work_create(request):
    """Фіксація виконаної роботи.
    Дата за замовчуванням — сьогодні, але можна змінити.
    Стрижки сортуються за статтю обраного клієнта.
    Форма відправляється ТІЛЬКИ кнопкою «Зафіксувати».
    При зміні клієнта — сторінка перезавантажується
    для сортування стрижок, але робота НЕ фіксується.
    """
    if request.method == "POST":
        form = CompletedWorkForm(request.POST)

        client_id = request.POST.get("client")
        if client_id:
            form.sort_haircuts_for_client(client_id)

        if form.is_valid():
            client = form.cleaned_data["client"]
            haircut = form.cleaned_data["haircut"]
            branch = form.cleaned_data["branch"]
            work_date = form.cleaned_data["work_date"]
            try:
                work = create_completed_work(client, haircut, branch, work_date)
                messages.success(
                    request,
                    f"Роботу зафіксовано! Чек #{work.check_id}, "
                    f"сума: {work.final_price} грн",
                )
                return redirect("salon:invoice_detail", pk=work.pk)
            except ValueError as e:
                messages.error(request, str(e))
    else:
        # GET-запит: підтримка попереднього заповнення
        # при перезавантаженні (зміна клієнта)
        initial = {}

        if request.GET.get("client"):
            initial["client"] = request.GET.get("client")
        if request.GET.get("haircut"):
            initial["haircut"] = request.GET.get("haircut")
        if request.GET.get("branch"):
            initial["branch"] = request.GET.get("branch")
        if request.GET.get("work_date"):
            initial["work_date"] = request.GET.get("work_date")

        if initial:
            form = CompletedWorkForm(initial=initial)
        else:
            form = CompletedWorkForm()

        # Сортування стрижок за статтю клієнта
        client_id = request.GET.get("client")
        if client_id:
            form.sort_haircuts_for_client(client_id)

    return render(
        request,
        "salon/works/work_form.html",
        {
            "form": form,
            "title": "Фіксація виконаної роботи",
        },
    )


# ──────────────── Рахунок-фактура ────────


def invoice_detail(request, pk):
    work = get_object_or_404(
        CompletedWork.objects.select_related("client__category", "haircut", "branch"),
        pk=pk,
    )
    base_price = get_current_price(work.haircut, work.branch) or work.final_price
    discount_percent = work.discount_percent
    discount_amount = base_price - work.final_price

    return render(
        request,
        "salon/invoices/invoice_detail.html",
        {
            "work": work,
            "base_price": base_price,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount,
        },
    )


# ──────────────── Звіти ──────────────────


def report_general(request):
    form = ReportFilterForm(request.GET or None)
    works = CompletedWork.objects.none()
    total_income = 0

    if form.is_valid():
        date_from = form.cleaned_data["date_from"]
        date_to = form.cleaned_data["date_to"]

        works = CompletedWork.objects.select_related(
            "client", "haircut", "branch"
        ).filter(work_date__gte=date_from, work_date__lte=date_to)

        total_income = works.aggregate(total=Sum("final_price"))["total"] or 0

    return render(
        request,
        "salon/reports/report_general.html",
        {
            "form": form,
            "works": works,
            "total_income": total_income,
        },
    )


def report_branch(request):
    form = ReportBranchFilterForm(request.GET or None)
    works = CompletedWork.objects.none()
    total_income = 0
    selected_branches = Branch.objects.none()
    branch_totals = []

    if form.is_valid():
        date_from = form.cleaned_data["date_from"]
        date_to = form.cleaned_data["date_to"]
        selected_branches = form.cleaned_data["branches"]

        works = CompletedWork.objects.select_related(
            "client", "haircut", "branch"
        ).filter(
            work_date__gte=date_from,
            work_date__lte=date_to,
            branch__in=selected_branches,
        )

        total_income = works.aggregate(total=Sum("final_price"))["total"] or 0

        for branch in selected_branches:
            branch_works = works.filter(branch=branch)
            branch_sum = branch_works.aggregate(total=Sum("final_price"))["total"] or 0
            branch_totals.append(
                {
                    "branch": branch,
                    "count": branch_works.count(),
                    "total": branch_sum,
                }
            )

    return render(
        request,
        "salon/reports/report_branch.html",
        {
            "form": form,
            "works": works,
            "total_income": total_income,
            "selected_branches": selected_branches,
            "branch_totals": branch_totals,
        },
    )
