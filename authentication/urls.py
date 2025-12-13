from django.urls import path
from authentication.views import check_admin, login, register, logout

app_name = 'authentication'

urlpatterns = [
    path('login/', login, name='login'),
    path('register/', register, name='register'),
    path('logout/', logout, name='logout'),
<<<<<<< HEAD
]   
=======
    path('check-admin/', check_admin, name='check_admin'),
]
>>>>>>> 4719009ab5d84d192e198f89cce3945d37e566a6
