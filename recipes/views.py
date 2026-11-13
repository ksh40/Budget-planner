from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction, IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from notifications.models import Notification
from notifications.services import notify, notify_staff
from plan.utils import get_budget
from wangapi.utils import decorate_recipes

from .forms import ChefApplicationForm, RecipeForm, RecipeReportForm, check_photos
from .models import ChefProfile, Recipe, RecipePhoto,RecipeReport, Status
from django.urls import reverse

PAGE_SIZE = 10


def _plain(amount):
    return f"{amount.normalize():f}"


def recipe_list(request):
    
    amount, show_all = get_budget(request)
    amount = min(amount, Decimal(10**9))

    live = Recipe.objects.live().select_related("chef__user").prefetch_related("photos")
    meal = request.GET.get("meal", "")
    if meal in Recipe.Meal.values:
        live = live.filter(meal_type=meal)
    else:
        meal = ""
    skill = request.GET.get("skill", "")
    if skill in Recipe.SkillLevel.values:
        live = live.filter(skill_level=skill)
    else:
        skill = ""
    if show_all:
        qs = live.order_by("price", "-created_at")
    elif amount > 0:
        qs = live.within_budget(amount).order_by("-price", "-created_at")  
    else:
        qs = live.none()

    page_number = request.GET.get("page")
    focus = request.GET.get("focus", "")
    if not page_number and focus.isascii() and focus.isdigit():
        ids = list(qs.values_list("pk", flat=True)) 
        if int(focus) in ids:
            page_number = ids.index(int(focus)) // PAGE_SIZE + 1
    page = Paginator(qs, PAGE_SIZE).get_page(page_number)
    recipes = list(page.object_list)
    for recipe in recipes:
        recipe.change = amount - recipe.price
    decorate_recipes(request.user, recipes)

    params = {}
    if amount > 0:
        params["amount"] = _plain(amount)
    if show_all:
        params["all"] = 1
    filter_hidden = {**params, **({"meal": meal} if meal else {})}
    if skill:
        params["skill"] = skill
    meal_links = [{"label": "All", "url": "?" + urlencode(params), "active": not meal}]
    for value, label in Recipe.Meal.choices:
        meal_links.append({
            "label": label,
            "url": "?" + urlencode({**params, "meal": value}),
            "active": meal == value,
        })
    base = urlencode({**params, **({"meal": meal} if meal else {})})

    chef = None
    if request.user.is_authenticated:
        chef = ChefProfile.objects.filter(user=request.user).first()
    post_url = reverse("recipes:create") if chef and chef.is_approved else reverse("recipes:apply")

    return render(request, "recipes/recipe_list.html", {
        "recipes": recipes,
        "page_obj": page,
        "amount": amount,
        "show_all": show_all,
        "show_change": not show_all,
        "meal": meal,
        "skill": skill,
        "skill_choices": Recipe.SkillLevel.choices,
        "filter_hidden": filter_hidden.items(),
        "meal_links": meal_links,
        "page_prefix": f"?{base}&" if base else "?",
        "show_all_url": "?all=1",
        "post_url": post_url,
    })


@login_required(login_url="wangapi_login")
def apply(request):
    chef = ChefProfile.objects.filter(user=request.user).first()
    if chef and chef.is_approved:
        return redirect("recipes:create")

    form = ChefApplicationForm(request.POST or None, instance=chef)
    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.status = Status.PENDING
        obj.moderator_note = ""
        obj.submitted_at = timezone.now()
        obj.save()
        notify(
            request.user,
            "We got your links. You will get a notification once you are approved.",
            kind=Notification.Kind.VERIFICATION,
        )
        notify_staff(
            f"New cook application from {request.user.username}.",
            reverse("admin:recipes_chefprofile_change", args=[obj.pk]),
        )
        return redirect("recipes:list")
    return render(request, "recipes/apply.html", {"form": form, "chef": chef})


@login_required(login_url="wangapi_login")
def recipe_create(request):
    chef = ChefProfile.objects.filter(user=request.user).first()
    if chef is None or not chef.is_approved:
        return redirect("recipes:apply")

    form = RecipeForm(request.POST or None)
    photo_errors = []
    if request.method == "POST":
        files = request.FILES.getlist("photos")
        try:
            files = check_photos(files)
        except ValidationError as error:
            photo_errors = error.messages
        if form.is_valid() and not photo_errors:
            with transaction.atomic():
                recipe = form.save(commit=False)
                recipe.chef = chef
                recipe.status = Status.APPROVED
                recipe.save()
                for position, f in enumerate(files):
                    RecipePhoto.objects.create(recipe=recipe, image=f, position=position)
            notify(
                request.user,
                f"Your recipe \u201c{recipe.title}\u201d iko live.",
                kind=Notification.Kind.RECIPE,
            )
            notify_staff(
                f"New recipe \u201c{recipe.title}\u201d from {request.user.username}.",
                reverse("admin:recipes_recipe_change", args=[recipe.pk]),
            )
            return redirect("wangapi_profile")
    return render(request, "recipes/recipe_form.html", {"form": form, "photo_errors": photo_errors})


@login_required(login_url="wangapi_login")
def recipe_edit(request, pk):
    recipe = get_object_or_404(
        Recipe.objects.prefetch_related("photos"), pk=pk, chef__user=request.user
    )
    existing = list(recipe.photos.all())
    form = RecipeForm(request.POST or None, instance=recipe)
    photo_errors = []

    if request.method == "POST":
        remove_ids = {int(i) for i in request.POST.getlist("remove_photo") if i.isdigit()}
        keep = [p for p in existing if p.pk not in remove_ids]
        files = request.FILES.getlist("photos")
        try:
            files = check_photos(files, keep=len(keep))
        except ValidationError as error:
            photo_errors = error.messages
        if form.is_valid() and not photo_errors:
            with transaction.atomic():
                recipe = form.save() 
                for p in existing:
                    if p.pk in remove_ids:
                        p.delete()
                position = 0
                for p in keep:
                    if p.position != position:
                        p.position = position
                        p.save(update_fields=["position"])
                    position += 1
                for f in files:
                    RecipePhoto.objects.create(recipe=recipe, image=f, position=position)
                    position += 1
            notify(
                request.user,
                f"Your recipe \u201c{recipe.title}\u201d was updated.",
                kind=Notification.Kind.RECIPE,
            )
            notify_staff(
                f"Recipe \u201c{recipe.title}\u201d was edited by {request.user.username}.",
                reverse("admin:recipes_recipe_change", args=[recipe.pk]),
            )
            return redirect("wangapi_profile")
        

    return render(request, "recipes/recipe_form.html", {
        "form": form, "photo_errors": photo_errors, "recipe": recipe, "photos": existing,
    })


@login_required(login_url="wangapi_login")
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, chef__user=request.user)
    if request.method == "POST":
        recipe.delete()
        return redirect("wangapi_profile")
    return render(request, "recipes/recipe_confirm_delete.html", {"recipe": recipe})


@login_required(login_url="wangapi_login")
def recipe_report(request, pk):
    recipe = get_object_or_404(Recipe.objects.live().select_related("chef__user"), pk=pk)
    if recipe.chef.user_id == request.user.id:
        return redirect("recipes:list")
    if RecipeReport.objects.filter(recipe=recipe, user=request.user).exists():
        notify(
            request.user,
            f"You already reported \u201c{recipe.title}\u201d. We are looking at it.",
            kind=Notification.Kind.RECIPE,
        )
        return redirect("recipes:list")

    form = RecipeReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        report = form.save(commit=False)
        report.recipe = recipe
        report.user = request.user
        try:
            report.save()
        except IntegrityError:        
            return redirect("recipes:list")
        notify(request.user, "Thanks for the report. We will look at it.",
               kind=Notification.Kind.RECIPE)
        notify_staff(
            f"Recipe \u201c{recipe.title}\u201d was reported ({report.get_reason_display()}).",
            reverse("admin:recipes_recipe_change", args=[recipe.pk]),
        )
        return redirect("recipes:list")
    return render(request, "recipes/report.html", {"form": form, "recipe": recipe})
