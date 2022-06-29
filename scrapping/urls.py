from django.urls import path
from . import views

app_name = 'scrapping'
urlpatterns = [
    path('', views.index, name='index'),
    path('<int:res_id>/', views.detail, name='detail')
]
