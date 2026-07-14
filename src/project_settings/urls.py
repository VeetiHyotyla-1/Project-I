from django.contrib import admin
from django.urls import path, include  
from django.shortcuts import redirect
from banking_app import views

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('view_statement', account_id=1)
    return redirect('login')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('statement/<int:account_id>/', views.view_statement, name='view_statement'),
    path('profile/save/', views.save_payment_profile, name='save_payment_profile'),
    path('transactions/search/', views.search_transactions, name='search_transactions'),
    path('withdrawal/process/', views.process_withdrawal, name='process_withdrawal'),
    path('', root_redirect),
]