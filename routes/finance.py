"""
Finance Routes - Semester fee and payment tracking for I-SAS
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app import db
from models.database import Finance

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')


@finance_bp.route('/')
@login_required
def index():
    """View finance dashboard with semester fees and payments"""
    transactions = current_user.finances.order_by(Finance.transaction_date.desc()).all()
    
    # Group by semester
    semesters = {}
    for t in transactions:
        sem = t.semester or "Uncategorized"
        if sem not in semesters:
            semesters[sem] = {'fee': 0, 'paid': 0, 'items': []}
        semesters[sem]['items'].append(t)
        if t.category == 'fee':
            semesters[sem]['fee'] += t.amount
        elif t.category == 'payment':
            semesters[sem]['paid'] += t.amount
    
    # Calculate progress for each semester
    for sem_name, data in semesters.items():
        if data['fee'] > 0:
            data['progress'] = min(100, (data['paid'] / data['fee']) * 100)
            data['remaining'] = max(0, data['fee'] - data['paid'])
        else:
            data['progress'] = 0
            data['remaining'] = 0
    
    # Overall totals
    total_fees = sum(f.amount for f in transactions if f.category == 'fee')
    total_paid = sum(f.amount for f in transactions if f.category == 'payment')
    balance = total_fees - total_paid
    
    return render_template('finance.html',
                         transactions=transactions,
                         semesters=semesters,
                         total_fees=total_fees,
                         total_paid=total_paid,
                         balance=balance)


@finance_bp.route('/set-fee', methods=['GET', 'POST'])
@login_required
def set_semester_fee():
    """Set semester fee amount"""
    if request.method == 'POST':
        try:
            new_fee = Finance(
                user_id=current_user.id,
                semester=request.form['semester'].strip(),
                category='fee',
                description=f"Semester Fee - {request.form['semester'].strip()}",
                amount=float(request.form['amount']),
                transaction_date=date.today(),
                is_paid=False
            )
            
            db.session.add(new_fee)
            db.session.commit()
            
            flash(f'Semester fee set: RM{new_fee.amount:.2f} 💰', 'success')
            return redirect(url_for('finance.index'))
            
        except Exception as e:
            flash(f'Error setting fee: {str(e)}', 'error')
    
    return render_template('finance_set_fee.html')


@finance_bp.route('/add-payment', methods=['GET', 'POST'])
@login_required
def add_payment():
    """Add a payment (partial, full, or sponsored)"""
    if request.method == 'POST':
        try:
            payment_type = request.form['payment_type']
            
            new_payment = Finance(
                user_id=current_user.id,
                semester=request.form['semester'].strip(),
                category='payment',
                description=request.form['description'].strip() or f"Payment ({payment_type.title()})",
                amount=float(request.form['amount']),
                payment_type=payment_type,
                transaction_date=datetime.strptime(request.form['transaction_date'], '%Y-%m-%d').date(),
                is_paid=True,
                receipt_number=request.form.get('receipt_number', '').strip(),
                notes=request.form.get('notes', '').strip()
            )
            
            db.session.add(new_payment)
            db.session.commit()
            
            flash(f'Payment recorded: RM{new_payment.amount:.2f} ✅', 'success')
            return redirect(url_for('finance.index'))
            
        except Exception as e:
            flash(f'Error adding payment: {str(e)}', 'error')
    
    # Get list of semesters with fees
    fees = Finance.query.filter_by(user_id=current_user.id, category='fee').all()
    semesters = list(set(f.semester for f in fees))
    
    return render_template('finance_add_payment.html', 
                         semesters=semesters,
                         payment_types=Finance.PAYMENT_TYPES)


@finance_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_transaction(id):
    """Delete a transaction"""
    transaction = Finance.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    
    db.session.delete(transaction)
    db.session.commit()
    
    flash('Transaction deleted 🗑️', 'success')
    return redirect(url_for('finance.index'))


@finance_bp.route('/summary')
@login_required
def summary():
    """Get finance summary (for dashboard widget)"""
    transactions = current_user.finances.all()
    
    total_fees = sum(f.amount for f in transactions if f.category == 'fee')
    total_paid = sum(f.amount for f in transactions if f.category == 'payment')
    
    return jsonify({
        'total_fees': total_fees,
        'total_paid': total_paid,
        'balance': total_fees - total_paid,
        'percentage_paid': round((total_paid / total_fees * 100) if total_fees > 0 else 0, 1)
    })
