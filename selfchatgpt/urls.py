from django.urls import path
from django.contrib import admin
from . import views

app_name = 'selfchatgpt'
urlpatterns = [

    path('', views.index, name='index'),
    path('start/', views.start_new_session_view, name='start_new_session'),
    path('chat/', views.chat, name='chat'),
    path('upload_csv/', views.upload_csv_for_users, name='upload_csv'),
    path('faqs/', views.faq_list, name='faq_list'),
    path('history/', views.history_list, name='history_list')
]
