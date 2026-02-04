"""
Exam Checker Routes for Student Assistant System
Handles carry mark and final exam calculations
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models.database import Result, Subject
from app import db

# Create blueprint
exam_bp = Blueprint('exam', __name__)


@exam_bp.route('/exam-check', methods=['GET', 'POST'])
@login_required
def index():
    """
    Exam checker page.
    
    Calculates:
    - Minimum carry mark needed (35%)
    - Minimum final exam mark needed (35%)
    - Whether student has passed requirements
    
    GET: Display checker form and history
    POST: Calculate and save result
    """
    # Get existing results
    results = Result.query.filter_by(user_id=current_user.id)\
        .order_by(Result.updated_at.desc()).all()
    
    # Get user's subjects for dropdown
    subjects = Subject.query.filter_by(user_id=current_user.id).all()
    
    calculation = None
    
    if request.method == 'POST':
        subject_name = request.form.get('subject_name', '').strip()
        carry_mark = request.form.get('carry_mark', type=float)
        carry_max = request.form.get('carry_max', 40, type=float)
        final_mark = request.form.get('final_mark', type=float)
        final_max = request.form.get('final_max', 60, type=float)
        save_result = request.form.get('save_result', False) == 'on'
        
        # Validation
        if not subject_name:
            flash('Please enter the subject name.', 'error')
            return render_template('exam_check.html',
                                 results=results,
                                 subjects=subjects)
        
        if carry_max <= 0 or final_max <= 0:
            flash('Maximum marks must be greater than 0.', 'error')
            return render_template('exam_check.html',
                                 results=results,
                                 subjects=subjects)
        
        # Calculate requirements
        min_carry_needed = carry_max * 0.35
        min_final_needed = final_max * 0.35
        
        # Calculate percentages
        carry_percentage = (carry_mark / carry_max * 100) if carry_mark is not None else None
        final_percentage = (final_mark / final_max * 100) if final_mark is not None else None
        
        # Check if passed
        passed_carry = carry_percentage >= 35 if carry_percentage is not None else None
        passed_final = final_percentage >= 35 if final_percentage is not None else None
        
        # Calculate total
        total_mark = 0
        total_max = carry_max + final_max
        if carry_mark is not None:
            total_mark += carry_mark
        if final_mark is not None:
            total_mark += final_mark
        
        total_percentage = (total_mark / total_max * 100) if total_max > 0 else 0
        
        # Determine overall status
        status = 'incomplete'
        status_message = ''
        
        if carry_percentage is not None and final_percentage is not None:
            if passed_carry and passed_final:
                status = 'passed' if total_percentage >= 50 else 'conditional'
                if status == 'passed':
                    status_message = '✅ Congratulations! You have passed this subject!'
                else:
                    status_message = '⚠️ You passed both components but need 50% overall to pass the subject.'
            elif not passed_carry:
                status = 'failed'
                status_message = f'❌ Your carry mark ({carry_percentage:.1f}%) is below 35%. You need at least {min_carry_needed:.1f} marks.'
            elif not passed_final:
                status = 'failed'
                status_message = f'❌ Your final exam ({final_percentage:.1f}%) is below 35%. You need at least {min_final_needed:.1f} marks.'
        elif carry_percentage is not None:
            if passed_carry:
                # Calculate what's needed in final
                needed_for_pass = max(min_final_needed, (50 - carry_mark) if (50 - carry_mark) > 0 else min_final_needed)
                status_message = f'📊 Carry mark passed! You need at least {needed_for_pass:.1f}/{final_max} in final exam.'
            else:
                status = 'at_risk'
                status_message = f'⚠️ Your carry mark ({carry_percentage:.1f}%) is below 35%. This is below passing requirement.'
        
        calculation = {
            'subject': subject_name,
            'carry': {
                'mark': carry_mark,
                'max': carry_max,
                'percentage': carry_percentage,
                'min_needed': min_carry_needed,
                'passed': passed_carry
            },
            'final': {
                'mark': final_mark,
                'max': final_max,
                'percentage': final_percentage,
                'min_needed': min_final_needed,
                'passed': passed_final
            },
            'total': {
                'mark': total_mark,
                'max': total_max,
                'percentage': total_percentage
            },
            'status': status,
            'status_message': status_message
        }
        
        # Save to database if requested
        if save_result and subject_name:
            existing = Result.query.filter_by(
                user_id=current_user.id,
                subject_name=subject_name
            ).first()
            
            if existing:
                existing.carry_mark = carry_mark
                existing.carry_max = carry_max
                existing.final_mark = final_mark
                existing.final_max = final_max
                existing.calculate_total()
                flash(f'Result for {subject_name} updated!', 'success')
            else:
                result = Result(
                    user_id=current_user.id,
                    subject_name=subject_name,
                    carry_mark=carry_mark,
                    carry_max=carry_max,
                    final_mark=final_mark,
                    final_max=final_max
                )
                result.calculate_total()
                db.session.add(result)
                flash(f'Result for {subject_name} saved!', 'success')
            
            try:
                db.session.commit()
                results = Result.query.filter_by(user_id=current_user.id)\
                    .order_by(Result.updated_at.desc()).all()
            except Exception as e:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'error')
                print(f"Exam save error: {e}")
    
    return render_template('exam_check.html',
                         results=results,
                         subjects=subjects,
                         calculation=calculation)


@exam_bp.route('/exam-check/calculate', methods=['POST'])
@login_required
def calculate():
    """
    AJAX endpoint for quick calculation.
    Does not save to database.
    """
    data = request.get_json()
    
    carry_mark = data.get('carry_mark', 0)
    carry_max = data.get('carry_max', 40)
    final_mark = data.get('final_mark')
    final_max = data.get('final_max', 60)
    
    if carry_max <= 0 or final_max <= 0:
        return jsonify({'error': 'Invalid maximum marks'}), 400
    
    # Calculate requirements
    min_carry = carry_max * 0.35
    min_final = final_max * 0.35
    
    # Calculate percentages
    carry_pct = (carry_mark / carry_max * 100) if carry_mark else 0
    final_pct = (final_mark / final_max * 100) if final_mark else 0
    
    # Calculate total
    total = (carry_mark or 0) + (final_mark or 0)
    total_max = carry_max + final_max
    total_pct = (total / total_max * 100) if total_max > 0 else 0
    
    # Determine what's needed to pass
    needed_final = 0
    if carry_mark is not None:
        # Need at least 35% in final
        needed_final = max(min_final, 50 - carry_mark if 50 > carry_mark else min_final)
    
    return jsonify({
        'carry': {
            'mark': carry_mark,
            'max': carry_max,
            'percentage': round(carry_pct, 2),
            'min_needed': round(min_carry, 2),
            'passed': carry_pct >= 35
        },
        'final': {
            'mark': final_mark,
            'max': final_max,
            'percentage': round(final_pct, 2),
            'min_needed': round(min_final, 2),
            'passed': final_pct >= 35 if final_mark else None,
            'needed_to_pass': round(needed_final, 2)
        },
        'total': {
            'mark': total,
            'max': total_max,
            'percentage': round(total_pct, 2),
            'passed': total_pct >= 50 and carry_pct >= 35 and (final_pct >= 35 if final_mark else True)
        }
    })


@exam_bp.route('/exam-check/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """Delete a result record"""
    result = Result.query.get_or_404(id)
    
    # Verify ownership
    if result.user_id != current_user.id:
        flash('Unauthorized action.', 'error')
        return redirect(url_for('exam.index'))
    
    subject_name = result.subject_name
    
    try:
        db.session.delete(result)
        db.session.commit()
        flash(f'Result for {subject_name} deleted.', 'info')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(f"Delete error: {e}")
    
    return redirect(url_for('exam.index'))
