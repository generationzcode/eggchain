from django.db import models


# Create your models here.
class Blockchain(models.Model):
    index = models.IntegerField()
    hash = models.CharField(max_length=200)
    timestamp = models.CharField(max_length=200)
    nonce = models.CharField(max_length=10)
    transactions = models.TextField()
    owner = models.CharField(max_length=100)
    pub_date = models.DateTimeField(auto_now_add=True)


class plots(models.Model):
    owner_public_key = models.CharField(max_length=1000)
    hash = models.CharField(max_length=200)
    coords = models.CharField(max_length=10)
    landscape = models.TextField()
    owner = models.CharField(max_length=100)
