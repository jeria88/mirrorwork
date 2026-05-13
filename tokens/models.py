from django.db import models
from django.conf import settings


class TokenBalance(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_balance'
    )
    balance = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.email}: {self.balance} tokens'

    def spend(self, amount, reason=''):
        if self.balance < amount:
            return False
        self.balance -= amount
        self.save()
        TokenTransaction.objects.create(user=self.user, amount=-amount, reason=reason)
        return True

    def credit(self, amount, reason=''):
        self.balance += amount
        self.save()
        TokenTransaction.objects.create(user=self.user, amount=amount, reason=reason)


class TokenTransaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='token_transactions'
    )
    amount = models.IntegerField()  # negativo = gasto, positivo = recarga
    reason = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f'{self.user.email} {sign}{self.amount} — {self.reason}'


class TokenPack(models.Model):
    name = models.CharField(max_length=60)
    tokens = models.IntegerField()
    price_usd = models.DecimalField(max_digits=6, decimal_places=2)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name}: {self.tokens} tokens por ${self.price_usd}'
