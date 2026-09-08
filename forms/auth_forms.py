"""
Authentication Forms for AgricLedger
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, TelField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError


class RegistrationForm(FlaskForm):
    """Form for user registration"""
    
    # Personal Information
    first_name = StringField('First Name', validators=[
        DataRequired(message='First name is required'),
        Length(min=2, max=50, message='Name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message='Last name is required'),
        Length(min=2, max=50, message='Name must be between 2 and 50 characters')
    ])
    
    # Contact Information
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    phone = TelField('Phone Number', validators=[
        DataRequired(message='Phone number is required'),
        Regexp(r'^\+?[0-9]{9,15}$', message='Please enter a valid phone number')
    ])
    
    # Location
    location = SelectField('Location', choices=[
        ('Harare', 'Harare'),
        ('Bulawayo', 'Bulawayo'),
        ('Mutare', 'Mutare'),
        ('Binga', 'Binga'),
        ('Murehwa', 'Murehwa'),
        ('Gweru', 'Gweru'),
        ('Masvingo', 'Masvingo'),
        ('Chinhoyi', 'Chinhoyi'),
        ('Kadoma', 'Kadoma'),
        ('Kwekwe', 'Kwekwe'),
        ('Other', 'Other')
    ], validators=[DataRequired(message='Please select your location')])
    
    # Role Selection
    role = SelectField('I am a', choices=[
        ('farmer', '🌾 Farmer'),
        ('admin', '👤 Admin')
    ], default='farmer', validators=[DataRequired(message='Please select your role')])
    
    # Password
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', 
               message='Password must contain uppercase, lowercase, and number')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    
    # Terms & Conditions
    terms = BooleanField('I agree to the Terms and Conditions', validators=[
        DataRequired(message='You must agree to the terms')
    ])
    
    # Email validation will be handled in the route (app.py)


class LoginForm(FlaskForm):
    """Form for user login"""
    email = EmailField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')


class TwoFactorForm(FlaskForm):
    """Form for two-factor authentication"""
    code = StringField('Authentication Code', validators=[
        DataRequired(message='Please enter your 6-digit code'),
        Length(min=6, max=6, message='Please enter a valid 6-digit code'),
        Regexp(r'^[0-9]{6}$', message='Please enter a valid 6-digit code')
    ])