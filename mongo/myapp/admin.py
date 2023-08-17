from django.contrib import admin
from .models import CustomUser,Asset,excelImport,Document,Attachment,ArtWorks,SalesReport
admin.site.register(CustomUser)
admin.site.register(Asset)
admin.site.register(excelImport)
admin.site.register(Document)
admin.site.register(Attachment)
admin.site.register(ArtWorks)
admin.site.register(SalesReport)


# Register your models here.

