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
        # --- BEFORE SCREENSHOT: Broken access control (fetches any account by ID) ---
        # account = Account.objects.get(pk=account_id)
        
        # --- AFTER SCREENSHOT: Safe access control checking owner ---
        account = Account.objects.get(pk=account_id)
        if account.owner != request.user:
            return HttpResponseForbidden("Unauthorized to view this statement.")
            
    except Account.DoesNotExist:
        return redirect('/')
        
    transactions = Transaction.objects.filter(account=account)
    
    # --- FLAW 4: Fetch payment profile data for rendering ---
    profile = PaymentProfile.objects.filter(user=request.user).first()
    card_number = None
    
    if profile:
        try:
            cipher_suite = Fernet(settings.ENCRYPTION_KEY)
            decrypted_card = cipher_suite.decrypt(profile.encrypted_card).decode()
            
            # --- BEFORE SCREENSHOT (FLAW 4): Plaintext raw sensitive data exposure (COMMENTED OUT) ---
            # card_number = decrypted_card
            
            # --- AFTER SCREENSHOT (FLAW 4): Masked card number display (ACTIVE) ---
            card_number = f"**** **** **** {decrypted_card[-4:]}" if len(decrypted_card) >= 4 else decrypted_card
            
        except Exception:
            card_number = "Error decrypting card data"

    return render(request, 'banking_app/statement.html', {
        'account': account, 
        'transactions': transactions,
        'card_number': card_number
    })

# ==========================================
# FLAW 2: Cryptographic Protection at Rest
# ==========================================
@login_required
def save_payment_profile(request):
    if request.method == 'POST':
        card_number = request.POST.get('card_number')
        if card_number:
            # --- BEFORE SCREENSHOT: Plaintext save ---
            # encrypted_data = card_number.encode()
            
            # --- AFTER SCREENSHOT: Symmetric encryption ---
            cipher_suite = Fernet(settings.ENCRYPTION_KEY)
            encrypted_data = cipher_suite.encrypt(card_number.encode())
            
            profile = PaymentProfile(user=request.user, encrypted_card=encrypted_data)
            profile.save()
            
    # Safe back-reference lookup to redirect back to the user's statement page
    user_account = Account.objects.filter(owner=request.user).first()
    if user_account:
        return redirect(f'/statement/{user_account.id}/')
    return redirect('/')

# ==========================================
# FLAW 3: SQL Injection (Injection)
# ==========================================
@login_required
def search_transactions(request):
    query = request.GET.get('q', '')
    
    # --- BEFORE SCREENSHOT: Raw query string execution ---
    # raw_sql = f"SELECT * FROM banking_app_transaction WHERE description = '{query}'"
    # results = Transaction.objects.raw(raw_sql)
    
    # --- AFTER SCREENSHOT: Parameterized Django ORM ---
    results = Transaction.objects.filter(description__iexact=query)
    
    return render(request, 'banking_app/results.html', {'results': results, 'query': query})

# ==========================================
# FLAW 5: Broken Access Control (Missing Authentication)
# ==========================================
# --- BEFORE SCREENSHOT: Comment out the decorator below to allow public access ---
# @login_required

# --- AFTER SCREENSHOT: Restrict access using authentication (ACTIVE) ---
@login_required
def view_all_accounts(request):
    
    # --- AFTER SCREENSHOT: Uncomment the lines below to restrict access (ACTIVE) ---
    if not request.user.is_staff:
        return HttpResponseForbidden("Access Denied: Administrative privileges required.")

    accounts = Account.objects.all()
    html = """
    <html>
    <head><title>Admin Panel - Master Account Directory</title></head>
    <body style="font-family: Arial; margin: 40px; background-color: #fbfbfc;">
        <h1 style="color: #c0392b;">System Admin: Account Registry</h1>
        <p>Warning: Internal use only. Confidential records.</p>
        <hr>
        <ul>
    """
    for acc in accounts:
        html += f"<li style='font-size: 18px; margin: 10px 0;'>User: <strong>{acc.owner.username}</strong> | Balance: <strong style='color: #27ae60;'>${acc.balance}</strong></li>"
    
    html += """
        </ul>
    </body>
    </html>
    """
    return HttpResponse(html)