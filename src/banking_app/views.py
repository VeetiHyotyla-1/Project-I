from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from cryptography.fernet import Fernet
from django.conf import settings
from django.db import connection  
from django.views.decorators.csrf import csrf_exempt 
from .models import Account, PaymentProfile, Transaction

# ==========================================
# FLAW 1: IDOR / Access Control
# ==========================================
@login_required
def view_statement(request, account_id):
    try:
        account = Account.objects.get(pk=account_id)
        
        # --- BEFORE SCREENSHOT: 
        if account.owner != request.user:
            return HttpResponseForbidden("Unauthorized to view this statement.")
        # --------------------------------------------------
        
    except Account.DoesNotExist:
        return redirect('/')
        
    transactions = Transaction.objects.filter(account=account)
    return render(request, 'banking_app/statement.html', {'account': account, 'transactions': transactions})

# ==========================================
# FLAW 2: Cryptographic Protection at Rest
# ==========================================
@login_required
def save_payment_profile(request):
    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        if card_number:
            # --- BEFORE SCREENSHOT: Un-comment line below to save plaintext ---
            # encrypted_data = card_number.encode()
            
            # --- AFTER SCREENSHOT: Use secure symmetric keys ---
            cipher_suite = Fernet(settings.ENCRYPTION_KEY)
            encrypted_data = cipher_suite.encrypt(card_number.encode())
            
            profile = PaymentProfile(user=request.user, encrypted_card=encrypted_data)
            profile.save()
    return redirect('/')

# ==========================================
# FLAW 3: SQL Injection (Injection)
# ==========================================
@login_required
def search_transactions(request):
    query = request.GET.get('q', '')
    
    # --- BEFORE SCREENSHOT: Raw raw string injection query ---
    # raw_sql = f"SELECT * FROM banking_app_transaction WHERE description = '{query}'"
    # results = Transaction.objects.raw(raw_sql)
    
    # --- AFTER SCREENSHOT: Safe Django ORM (Auto-parameterized) ---
    results = Transaction.objects.filter(description__iexact=query)
    
    return render(request, 'banking_app/results.html', {'results': results, 'query': query})

# ==========================================
# FLAW 5: CSRF Validation Missing
# ==========================================
@login_required
# --- BEFORE SCREENSHOT: Un-comment line below to bypass security token check ---
def process_withdrawal(request):
    if request.method == 'POST':
        try:
            account = Account.objects.get(owner=request.user)
            amount = int(request.POST.get('amount', 0))
            if amount > 0 and account.balance >= amount:
                account.balance -= amount
                account.save()
        except (Account.DoesNotExist, ValueError):
            pass
    return redirect('/')