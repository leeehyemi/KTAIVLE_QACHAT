from django.contrib import admin
from django.db import models

# Create your models here.
class chatHistory(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    question = models.TextField()
    answer = models.TextField()
    
    def __str__(self):
        return f"{self.datetime}: {self.question[:50]}"
    
    class Meta:
        indexes = [
            models.Index(fields=['datetime']),
            models.Index(fields=['question']),
            models.Index(fields=['answer']),
        ]

class User(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name
    
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=50)

class faq(models.Model):
    answer = models.TextField()
    
    def __str__(self):
        return self.answer[:50]