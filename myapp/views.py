from django.shortcuts import render,get_object_or_404,redirect
from .models import *
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from django.http import HttpResponse
from io import BytesIO
import os
from django.conf import settings

# Register View
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, 'register.html')

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email
        )
        user.save()
        messages.success(request, "Account created successfully..")
        return redirect('login')
    
    return render(request, 'register.html')

# login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('blog_list')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
        
    if 'next' in request.GET:
        messages.info(request, "You must log in to access that page.")
    return render(request, 'login.html')


# logout view
def logout_view(request):
    logout(request)
    return redirect('login')

# portfolio
def public_portfolio(request):
    if request.user.is_authenticated:
        return redirect('blog_list')
    return render(request, 'portfolio.html')

def explore_view(request):
    posts = Blogpost.objects.all().order_by('-created_at')
    return render(request, 'explore.html', {'posts': posts})


@login_required(login_url='login')
def create_blog_post_form(request):
    if request.method == 'POST':
        title = request.POST['title']
        summary = request.POST['summary']
        content = request.POST['content']
        image = request.FILES.get('image')

        Blogpost.objects.create(
            user=request.user, 
            title=title,
            summary=summary,
            content=content,
            image=image
        )
        return redirect('blog_list')
    return render(request, 'upload_blog.html')


@login_required(login_url='login')
def blog_update(request, post_id):
    post = get_object_or_404(Blogpost, id=post_id)

    if post.user != request.user:
        return redirect('explore')

    if request.method == 'POST':
        post.title = request.POST.get('title')
        post.summary = request.POST.get('summary')
        post.content = request.POST.get('content')
        if 'image' in request.FILES:
            post.image = request.FILES['image']
        post.save()
        return redirect('blog_detail', post_id=post.id)

    return render(request, 'edit_blog.html', {'post': post})


@login_required(login_url='login')
def blog_delete(request, post_id):
    post = get_object_or_404(Blogpost, id=post_id)
    if post.user != request.user:
        return redirect('explore')
    post.delete()
    return redirect('blog_list')


@login_required(login_url='login')
def list(request):
    post_title = "Recent posts"
    posts = Blogpost.objects.filter(user=request.user).order_by('-created_at')
    return render(request,'index.html',{'post_title':post_title, 'posts':posts})


@login_required(login_url='login')
def detail(request,post_id):
    post = get_object_or_404(Blogpost, pk=post_id)
    comments = Comment.objects.filter(post=post).order_by('-created_at')

    # like
    has_liked = False
    if request.user.is_authenticated:
        has_liked = post.like_set.filter(user=request.user).exists()

    # comment
    if request.method == 'POST' and 'comment' in request.POST:
        content = request.POST.get('comment')
        if content:
            Comment.objects.create(user=request.user, post=post, content=content)
            return redirect('blog_detail', post_id=post_id)

    return render(request, 'detail.html', {
        'post': post,
        'has_liked': has_liked,
        'comments': comments,
    })


@login_required
def toggle_like(request, post_id):
    post = get_object_or_404(Blogpost, id=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
    return redirect('blog_detail', post_id=post_id)


@login_required(login_url='login')
def profile_view(request):
    posts = Blogpost.objects.filter(user=request.user).order_by('-created_at')

    if request.method == 'POST' and request.FILES.get('avatar'):
        # ✅ Safe path based on MEDIA_ROOT
        avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
        
        # ✅ Create folder if it doesn't exist
        os.makedirs(avatar_dir, mode=0o777, exist_ok=True)

        profile = request.user.userprofile
        profile.avatar = request.FILES['avatar']
        profile.save()

    return render(request, 'profile.html', {
        'user': request.user,
        'profile': request.user.userprofile,
        'posts': posts,
    })


@login_required(login_url='login')
def download_my_posts_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, f"{request.user.username}'s Blog Posts")
    y -= 30

    posts = Blogpost.objects.filter(user=request.user).order_by('-created_at')

    if not posts:
        p.setFont("Helvetica", 12)
        p.drawString(50, y, "No blog posts found.")
    else:
        for post in posts:
            if y < 100:
                p.showPage()
                y = height - 50
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, y, post.title)
            y -= 20
            p.setFont("Helvetica", 12)
            summary = post.summary if post.summary else ''
            p.drawString(50, y, f"Summary: {summary[:100]}")
            y -= 20
            p.drawString(50, y, f"Created at: {post.created_at.strftime('%Y-%m-%d %H:%M')}")
            y -= 30

    p.showPage()
    p.save()    
    buffer.seek(0)

    return HttpResponse(buffer, content_type='application/pdf')



