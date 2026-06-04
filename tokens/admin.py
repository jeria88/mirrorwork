from django.contrib import admin

from .models import MpPurchase, Mission, MissionCompletion, PayPalPurchase, TokenBalance, TokenPack, TokenTransaction


@admin.register(TokenPack)
class TokenPackAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "fractones", "price_clp", "active", "order")
    list_editable = ("active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(TokenBalance)
class TokenBalanceAdmin(admin.ModelAdmin):
    list_display = ("user", "permanent", "monthly", "balance", "monthly_last_renewed")
    readonly_fields = ("balance",)


@admin.register(TokenTransaction)
class TokenTransactionAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "reason", "source", "created_at")
    list_filter = ("source",)
    search_fields = ("user__email", "reason")


@admin.register(MpPurchase)
class MpPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "pack_slug", "fractones", "amount_clp", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "pack_slug", "mp_payment_id")
    readonly_fields = ("mp_raw",)


@admin.register(PayPalPurchase)
class PayPalPurchaseAdmin(admin.ModelAdmin):
    list_display = ("user", "pack_slug", "fractones", "amount_usd", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("user__email", "pack_slug", "pp_order_id")
    readonly_fields = ("pp_raw",)


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "fracton_reward", "prerequisite_slug", "active", "order")
    list_editable = ("active", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MissionCompletion)
class MissionCompletionAdmin(admin.ModelAdmin):
    list_display = ("user", "mission", "completed_at")
    search_fields = ("user__email",)
