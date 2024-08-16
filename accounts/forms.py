# from django.shortcuts import render, redirect
# from django.contrib.auth.forms import UserCreationForm
# from django.conf import settings
# from .forms import SignupForm

# from django import forms
# from .models import Profile


# def signup(request):
#     if request.method == 'POST':
#         form = SignupForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect(settings.LOGIN_URL)
#     else:
#         form = SignupForm()
#     return render(request, 'registration/signup.html',{'form':form})

# class SignupForm(UserCreationForm):
#     phone_number = forms.CharField()
#     address = forms.CharField()
#     class Meta(UserCreationForm.Meta):
#         fields = UserCreationForm.Meta.fields + ('email', )
#     def save(self):
#         user = super().save()
#         Profile.objects.create(user=user,
#                                 phone_number=self.cleaned_data['phone_number'],
#                                 address=self.cleaned_data['address'])
#         return user
from django.contrib.auth.forms import UserCreationForm 
from django import forms 
from .models import Profile

class SignupForm(UserCreationForm):
    phone_number = forms.CharField()
    address = forms.CharField()

    class Meta(UserCreationForm.Meta):
        fields = UserCreationForm.Meta.fields + ('email', )

    def save(self):
        user = super().save() 
        Profile.objects.create(user=user, 
                               phone_number=self.cleaned_data['phone_number'],
                               address=self.cleaned_data['address'])
        return user