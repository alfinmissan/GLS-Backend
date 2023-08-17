from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    id = models.BigAutoField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100,unique=True)
    designation = models.CharField(max_length=100)
    user_group = models.CharField(max_length=20)
    country = models.CharField(max_length=50)

class Asset(models.Model):
    name = models.CharField(max_length=20)
    photo = models.ImageField(upload_to='pics')
    type = models.CharField(max_length=20)

class Fonts(models.Model):
    name = models.CharField(max_length=150)
    font = models.FileField(upload_to='files')
    language = models.CharField(max_length=15)

#model for attach files and comments to the grid
class Attachment(models.Model):
    user = models.CharField(max_length=40)
    comment = models.CharField(max_length=500)
    attachment = models.FileField(upload_to='files',null=True)
    varient = models.CharField(max_length=40,null=False)
    datetime = models.DateTimeField(null=True)
#model for attch support documents to grid
class Document(models.Model):
    user = models.CharField(max_length=40)
    varient = models.CharField(max_length=20,null=False)
    attachment = models.FileField(upload_to='files', null=True)
    datetime = models.DateTimeField(null=True)
class excelImport(models.Model):
    file = models.FileField(upload_to='files')
# class notificationcount(models.Model):
#     user_groups = models.CharField(max_length=100)

class ArtWorks(models.Model):
    item = models.CharField(max_length=100)
    job = models.CharField(max_length=100)
    attachment = models.ImageField(upload_to='files',null=True)
    varient = models.CharField(max_length=100,null=False)
    datetime = models.DateTimeField(null=True)
class SalesReport(models.Model):
    file = models.FileField(upload_to='sales_reports')
    varient = models.CharField(max_length=100,null=False)
    datetime = models.DateTimeField(null=True)
