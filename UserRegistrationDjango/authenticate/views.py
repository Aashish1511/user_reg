from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.message import EmailMessage
from telnetlib import LOGOUT
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from urd import settings
import smtplib
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token

# Create your views here.
def home(request):
    return render(request,'authenticate/index.html')
    #return HttpResponse("Hello I am Working")
#Signup Function
def signup(request):

    if request.method == "POST":
        #username = request.POST.get('username')
        # import pdb;pdb.set_trace()
        username= request.POST['Username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        # import pdb;pdb.set_trace()

        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! please try some other username")
            return redirect('home')
        
        if User.objects.filter(email=email):
            messages.error(request, 'Email already exist!')
            return redirect('home')

        if len(username) > 10:
            messages.error(request, 'username should be under 10 characters')

        if pass1 != pass2:
            messages.error(request, 'pass1 is not same as pass2')

        if not username.isalnum():
            messages.error(request, 'password should have only letters and numbers')
            return redirect('home')
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = False
        myuser.save()

        messages.success(request, "Your account has been successfully created.")


        #welcome email
        # import pdb; pdb.set_trace()
        subject = 'Hi Welcome you to ATC'
        message = "hello"  +  myuser.first_name  + "! \n" + "Welcome to ATC!! \n Thank you for visiting our website \n also we have sent you welcome email, please confirm your email address in order to activate it. \n\n Thanking you, \n Aashish kumar"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)


        #Email address confirmation Email

        current_site = get_current_site(request)
        email_subject = "Confirm Your Email @ ATC -Django Login"
        message2 = render_to_string('email_confirmation.html',{
            'name': myuser.first_name,
            'domain': current_site.domain,
            'uid': urlsafe_b64encode(force_bytes(myuser.pk)),
            'token': generate_token.make_token(myuser)
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )
        email.fails_silently = True
        email.send()

        return redirect("signin")


    return render(request, "authenticate/signup.html")
#Signin Function
def signin(request):
    
    if request.method == "POST":
        # import pdb;pdb.set_trace()
        # user_name == request.POST['Username']
        # passwd == request.POST['pass1']
        # import pdb;pdb.set_trace()
        user = authenticate(username=request.POST['Username'], password=request.POST['pass1'])

        if user is not None:
            login(request, user)
            fname = user.first_name
            return render(request, "authenticate/index.html", {'fname': fname})

        else:
            messages.error(request, "Bad Credentials!")
            return redirect('home')
            
    return render(request, "authenticate/signin.html")
#Signout Function
def signout(request):
    logout(request)
    messages.success(request,"Logged Out Successfully")
    return redirect('home')
    #return render(request, 'authenticate/signout.html')

# ACCOUNT Activation function
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_b64decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        return redirect('home')
    else:
        return render(request, 'activation failed.html')