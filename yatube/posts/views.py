from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth import get_user_model
from django.views.decorators.cache import cache_page


User = get_user_model()
NUMBER_OF_POST = 10


def pag(queryset, request):
    """Paginator"""
    paginator = Paginator(queryset, NUMBER_OF_POST)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


@cache_page(20, key_prefix='page_index')
def index(request):
    post_list = Post.objects.all()
    page_obj = pag(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.filter(group=group)
    page_obj = pag(posts, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group', 'author')
    page_obj = pag(post_list, request)
    following = request.user.is_authenticated and (
        Follow.objects.filter(user=request.user, author=author).exists())
    context = {
        'page_obj': page_obj,
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    number_all = Post.objects.filter(author=post.author).count()
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'number_all': number_all,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
        )
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user.username)
    form = PostForm()
    context = {
        'form': form
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:post_detail', post_id)
    context = {
        'is_edit': True,
        'form': form,
        'post_id': post_id
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = pag(post_list, request)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = get_object_or_404(User, username=username)
    if request.user == user:
        return redirect('posts:profile', request.user.username)
    if not Follow.objects.filter(user=request.user, author=user).exists():
        Follow.objects.get_or_create(user=request.user, author=user)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=user)
    follow.delete()
    return redirect('posts:index')
