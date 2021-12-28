from flask import flash, redirect, render_template, url_for
from flask_login import login_user, login_required, logout_user

from . import auth
from .forms import RegistrationForm, LoginForm
from .. import db
from ..models import Member


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        member = Member(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            telephone=form.telephone.data,
            semester=form.semester.data,
            uni_reg_number=form.uni_reg_number.data,
            address=f"{form.city.data}, {form.address.data}"
        )

        db.session.add(member)
        db.session.commit()
        flash('You have successfully registered! You may now login.')

        # redirect to the login page
        return redirect(url_for('public.homepage'))

        # load registration template
    return render_template('register.html', form=form, title='Register')


@auth.route('/login', methods=['POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        # check whether member exists in the database and whether
        # the password entered matches the password in the database
        member = Member.query.filter_by(email=form.email.data).first()
        if member is not None and member.verify_password(
                form.password.data):
            # log employee in
            login_user(member)

            # redirect to the dashboard page after login
            return redirect(url_for('ca.dashboard'))

        # when login details are incorrect
        else:
            flash('Invalid email or password.')

    # load login template
    return render_template('index.html', form=form, title='Login')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    # redirect to the homepage
    return redirect(url_for('public.homepage'))