from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth.models import auth, User
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from datetime import date
from django.core.paginator import Paginator

from .models import Book, IssuedItem


# Create your views here.


# home view
def home(request):
    return render(request, "home.html")


# login view
def login(request):
    if request.method == "POST":  # if request is post then get username and password from request
        username = request.POST["username"]
        password = request.POST["password"]

        user = auth.authenticate(username=username, password=password)  # authenticate user

        if user is not None:
            auth.login(request, user)  # if user is authenticated then login user

            return redirect("/")  # redirect to home page

        else:
            messages.info(request, "Invalid Credential") # if user is not authenticated then
                                                         # show error message and redirect
            return redirect("login")                     # to login page

    else:
        return render(request, "login.html")  # if request is not post then render login page


# register view to register user
def register(request):
    if request.method == "POST":                    # if request is post then get user
        first_name = request.POST["first_name"]     # details from request
        last_name = request.POST["last_name"]
        username = request.POST["username"]
        email = request.POST["email"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 == password2:  # check if password and comfirm password matches

            if User.objects.filter(username=username).exists():   # check if username or email
                messages.info(request, "Username already exist")  # already exists
                return redirect("register")

            elif User.objects.filter(email=email).exists():     # check if email already exists
                messages.info(request, "Email already exist")
                return redirect("register")

            else:  # if username and email does not exits then create user
                user = User.objects.create_user(  # create user
                        first_name=first_name, 
                        last_name=last_name,
                        username=username,
                        email=email,
                        password=password1,
                        )

                user.save()  # save user

                return redirect("login")  # redirect to login page
        else:
            messages.info(request, "Password not matches")  # if password and confirm password does not matches
            return redirect("register")                     # then show error

    else:
        return render(request, "register.html")  # if request is not post then render register page


# logout view to logout user
def logout(request):
    auth.logout(request)  # logout and redirect to home page
    return redirect("/")


# issue view to issue book to user
@login_required(login_url="login")
def issue(request):
    if request.method == "POST":  # if request is post then get id from request
        book_id = request.POST["book_id"]
        current_book = Book.objects.get(id=book_id)
        book = Book.objects.filter(id=book_id)
        issue_item = IssuedItem.objects.create(
                user_id=request.user, book_id=current_book
                )
        issue_item.save()
        book.update(quantity=book[0].quantity - 1)

        messages.success(request, "完了しました")  # show success message and
                                                                # redirect to issue page
    my_items = IssuedItem.objects.filter(  # get all books which are not issued to user
            user_id=request.user,
            return_date__isnull=True
            ).values_list("book_id")

    books = Book.objects.exclude(id__in=my_items).filter(quantity__gt=0)

    return render(request, "issue_item.html", {"books": books})  # return issue page with books
                                                                 # that are not issued to user


# history view to show history of issued books to user
@login_required(login_url="login")
def history(request):
    my_items = IssuedItem.objects.filter(
            user_id=request.user
            ).order_by("-issue_date")

    paginator = Paginator(my_items, 10)  # paginate data

    page_number = request.GET.get("page")  # get page number from request
    show_data_final = paginator.get_page(page_number)

    return render(request, "history.html", {"books": show_data_final})  # return history page with
                                                                        # issued books to user


# return view to return book to library
@login_required(login_url="login")
def return_item(request):
    if request.method == "POST":  # if request is post then get book id from request
        book_id = request.POST["book_id"]  # get book id from request
        current_book = Book.objects.get(id=book_id)  # get book object
        
        book = Book.objects.filter(id=book_id)  # update book quantity
        book.update(quantity=book[0].quantity + 1)

        issue_item = IssuedItem.objects.filter(  # update return date of book and show success message
                user_id=request.user, 
                book_id=current_book,
                return_date__isnull=True
                )
        issue_item.update(return_date=date.today())
        messages.success(request, "Book returned successfully.")

    my_items = IssuedItem.objects.filter(  # get all books which are issued to user
            user_id=request.user,
            return_date__isnull=True
            ).values_list("book_id")

    books = Book.objects.exclude(~Q(id__in=my_items))  # get all books which are not issued to user

    params = {"books": books}  # return return page with books that are issued to user
    return render(request, "return_item.html", params)

