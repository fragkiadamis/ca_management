from flask import render_template, session, flash, request, redirect, url_for
from flask_login import login_required

from .. import ca
from .forms import ProfileForm, BooleanForm
from app.models import Member
from ... import db
from ...decorators import permissions_required


@ca.route('/members', methods=['GET', 'POST'])
@login_required
def list_members():
    display = request.args.get('display')
    members = None

    # Filter Members according to url parameter
    # TODO implement filters for basic users
    if display == 'pending':
        members = {'Pending': Member.query.filter(Member.is_verified == 0)}
    elif display == 'active':
        members = {'Active': Member.query.filter(Member.is_active == 1, Member.is_verified == 1)}
    elif display == 'inactive':
        members = {'Inactive': Member.query.filter(Member.is_active == 0, Member.is_verified == 1)}
    elif display == 'admin':
        members = {'Admin': Member.query.filter(Member.role == 'admin', Member.is_verified == 1)}
    elif display == 'ca_admin':
        members = {'CA Admin': Member.query.filter(Member.role == 'ca_admin', Member.is_verified == 1)}
    elif display == 'basic':
        members = {'Basic': Member.query.filter(Member.role == 'basic', Member.is_verified == 1)}
    elif display == 'role':
        all_members = Member.query.filter(Member.is_verified == 1)
        admins = [d for d in all_members if d.role == 'admin']
        ca_admins = [d for d in all_members if d.role == 'ca_admin']
        basics = [d for d in all_members if d.role == 'basic']
        members = {'Admins': admins, 'CA Admins': ca_admins, 'Basic': basics}
    elif display == 'status':
        all_members = Member.query.filter(Member.is_verified == 1)
        active = [d for d in all_members if d.is_active]
        inactive = [d for d in all_members if not d.is_active]
        members = {'Active': active, 'Inactive': inactive}
    else:
        members = {'Current': Member.query.filter(Member.is_verified == 1, Member.is_active == 1)}

    sess_user = {'id': session['_user_id'], 'username': session['_username'], 'roles': session['_user_roles']}
    return render_template('private/members.html', boolean_form=BooleanForm(), user=sess_user, members=members, title='Members', display=display)


@ca.route('/members/<int:member_id>', methods=['GET', 'POST'])
@login_required
def profile(member_id):
    sess_user = {'id': session['_user_id'], 'username': session['_username'], 'roles': session['_user_roles']}

    form = ProfileForm()
    member = Member.query.get_or_404(member_id)

    if form.validate_on_submit():
        if not member.verify_password(form.confirm_changes.data):
            flash('Invalid Password')
            return render_template('private/profile.html', form=form, user=sess_user, title='Profile')

        # Update member properties

        if form.password.data:
            member.password = form.password.data
        member.first_name = form.first_name.data
        member.last_name = form.last_name.data
        member.username = form.username.data
        member.email = form.email.data
        member.telephone = form.telephone.data
        member.city = form.city.data
        member.address = form.address.data
        db.session.commit()
        flash('You have successfully updated your profile.')

    return render_template('private/profile.html', form=form, member=member, user=sess_user, title='Profile')


@ca.route('/status/<int:member_id>', methods=['GET', 'POST'])
@login_required
@permissions_required(['Admin', 'CA Admin'])
def toggle_status(member_id):
    form = BooleanForm()
    display = request.args.get('display')

    if form.validate_on_submit():
        member = Member.query.get_or_404(member_id)
        member.is_active = form.status.data
        db.session.commit()

    return redirect(url_for('ca.list_members', display=display))


@ca.route('/verify/<int:member_id>', methods=['POST'])
@login_required
@permissions_required(['Admin', 'CA Admin'])
def verify(member_id):
    form = BooleanForm()
    if form.validate_on_submit():
        member = Member.query.get_or_404(member_id)
        if form.status.data:
            # Get last verified member's ca reg number and increase it to one and assign to new verified member
            last_member = Member.query.filter(Member.is_verified == 1).order_by(Member.id.desc()).first()
            incremental = int(''.join(x for x in last_member.ca_reg_number if x.isdigit())) + 1
            member.ca_reg_number = f'ca{incremental}'
            member.is_verified = member.is_active = 1
            db.session.commit()
        else:
            db.session.delete(member)
            db.session.commit()

    return redirect(url_for('ca.list_members', display='pending'))