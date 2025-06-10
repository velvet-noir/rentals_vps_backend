from django.db import models


class Service(models.Model):
    name = models.CharField(max_length=100)
    image = models.CharField(max_length=1024)
    mini_description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["id"]
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"
