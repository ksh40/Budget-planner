from django.contrib import admin
from django.db.models import Count
from .models import ChefProfile, Recipe, RecipePhoto, RecipeReport, Status


@admin.action(description="Approve selected")
def approve(modeladmin, request, queryset):
    for obj in queryset:
        obj.approve()


@admin.action(description="Reject selected (type the reason in Moderator note first)")
def reject(modeladmin, request, queryset):
    for obj in queryset:
        obj.reject(obj.moderator_note)


@admin.action(description="Remove reported recipes and notify the cook")
def remove_reported(modeladmin, request, queryset):
    count = 0
    for recipe in queryset:
        recipe.remove_for_report()
        count += 1
    modeladmin.message_user(request, f"Removed {count} recipe(s) and notified the cooks.")


@admin.register(ChefProfile)
class ChefProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("display_name", "user__username")
    actions = [approve, reject]

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            if obj.status == Status.APPROVED:
                obj.approve()
                return
            if obj.status == Status.REJECTED:
                obj.reject(obj.moderator_note)
                return
        super().save_model(request, obj, form, change)


class RecipePhotoInline(admin.TabularInline):
    model = RecipePhoto
    extra = 1
    max_num = 4


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "chef", "meal_type", "price", "status", "report_count", "created_at")
    list_filter = ("status", "meal_type")
    search_fields = ("title", "chef__user__username", "chef__display_name")
    inlines = [RecipePhotoInline]
    actions = [approve, reject, remove_reported]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_reports=Count("reports"))

    @admin.display(ordering="_reports", description="Reports")
    def report_count(self, obj):
        return obj._reports


@admin.register(RecipeReport)
class RecipeReportAdmin(admin.ModelAdmin):
    list_display = ("recipe", "user", "reason", "details", "resolved", "created_at")
    list_filter = ("resolved", "reason")
    actions = ["mark_resolved", "hide_recipes"]

    @admin.action(description="Mark selected as resolved")
    def mark_resolved(self, request, queryset):
        queryset.update(resolved=True)

    @admin.action(description="Hide the reported recipes (rejects them and notifies the cook)")
    def hide_recipes(self, request, queryset):
        seen = set()
        for report in queryset.select_related("recipe__chef__user"):
            if report.recipe_id not in seen:
                seen.add(report.recipe_id)
                report.recipe.reject("Removed after a report.")
        queryset.update(resolved=True)