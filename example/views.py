# example/views.py
# hackernews/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.contrib import messages

from .models import Story, Comment, Vote, UserProfile
from .forms import StoryForm, CommentForm, UserProfileForm

def home(request):
    stories = Story.objects.all().order_by('-score', '-created_at')
    paginator = Paginator(stories, 30)  # Show 30 stories per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hackernews/home.html', {'page_obj': page_obj})

def newest(request):
    stories = Story.objects.all().order_by('-created_at')
    paginator = Paginator(stories, 30)  # Show 30 stories per page
    
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'hackernews/newest.html', {'page_obj': page_obj})

def story_detail(request, pk):
    story = get_object_or_404(Story, pk=pk)
    comments = Comment.objects.filter(story=story, parent=None).order_by('created_at')
    
    # Get if the current user has voted for this story
    user_voted = False
    if request.user.is_authenticated:
        user_voted = Vote.objects.filter(user=request.user, story=story).exists()
    
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.user = request.user
            
            # Handle replies
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = get_object_or_404(Comment, pk=parent_id)
                comment.parent = parent_comment
            
            comment.save()
            return redirect('story_detail', pk=story.pk)
    else:
        form = CommentForm()
    
    return render(request, 'hackernews/story_detail.html', {
        'story': story,
        'comments': comments,
        'form': form,
        'user_voted': user_voted,
    })

@login_required
def submit_story(request):
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            return redirect('home')
    else:
        form = StoryForm()
    
    return render(request, 'hackernews/submit_story.html', {'form': form})

@login_required
def upvote_story(request, pk):
    story = get_object_or_404(Story, pk=pk)
    
    # Check if user already voted
    vote, created = Vote.objects.get_or_create(
        user=request.user,
        story=story,
        defaults={'vote_type': Vote.UPVOTE}
    )
    
    if not created:
        # User already voted, so we remove the vote
        vote.delete()
        story.calculate_score()
        return JsonResponse({'success': True, 'action': 'removed'})
    else:
        # Vote was created
        story.calculate_score()
        
        # Update user karma
        profile = UserProfile.objects.get_or_create(user=story.user)[0]
        profile.calculate_karma()
        
        return JsonResponse({'success': True, 'action': 'added'})

@login_required
def submit_comment(request, story_pk, parent_pk=None):
    story = get_object_or_404(Story, pk=story_pk)
    parent = None
    
    if parent_pk:
        parent = get_object_or_404(Comment, pk=parent_pk)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.story = story
            comment.user = request.user
            comment.parent = parent
            comment.save()
            
            # Update user karma
            profile = UserProfile.objects.get_or_create(user=request.user)[0]
            profile.calculate_karma()
            
            return redirect('story_detail', pk=story.pk)
    else:
        form = CommentForm()
    
    context = {
        'form': form,
        'story': story,
        'parent': parent,
    }
    return render(request, 'hackernews/submit_comment.html', context)

def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    # Get user's stories and comments
    stories = Story.objects.filter(user=user).order_by('-created_at')
    comments = Comment.objects.filter(user=user).order_by('-created_at')
    
    context = {
        'profile_user': user,
        'profile': profile,
        'stories': stories,
        'comments': comments,
    }
    return render(request, 'hackernews/user_profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'hackernews/edit_profile.html', {'form': form})

def search(request):
    query = request.GET.get('q', '')
    stories = []
    
    if query:
        stories = Story.objects.filter(title__icontains=query).order_by('-created_at')
    
    return render(request, 'hackernews/search.html', {
        'stories': stories,
        'query': query,
    })