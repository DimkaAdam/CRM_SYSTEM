from django.db import models

class Client(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True,null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Deals(models.Model):
    status_choices = [
        ('open','Open'),
        ('in_progress','In Progress'),
        ('closed','Closed'),
    ]

    client = models.ForeignKey(Client,on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    status = models.CharField(max_length=20, choices=status_choices, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class Task(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    due_date = models.DateField()
    completed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class PipeLine(models.Model):
    name = models.CharField(max_length=255, verbose_name="Sellers")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    stage = models.CharField(max_length=100,verbose_name="Stage")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created')
    updated_at = models.DateTimeField(auto_now=True,verbose_name='Updated')

    def __str__(self):
        return self.name
