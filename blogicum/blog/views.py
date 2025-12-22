from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    ListView,
    DetailView,
    UpdateView,
    CreateView,
    DeleteView,
)

from core.mixins import CommentMixinView
from core.utils import post_all_query, post_published_query, get_post_data
from .models import Post, User, Category, Comment
from .forms import UserEditForm, PostEditForm, CommentEditForm


# ======================
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ======================

def get_posts_metadata(queryset=None, is_author=False):
    """Фильтрация постов и подсчёт комментариев."""
    if queryset is None:
        queryset = Post.objects.all()

    if not is_author:
        queryset = queryset.filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now()
        )

    return queryset.annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def get_page_obj(request, queryset, per_page=10):
    """Пагинация."""
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# ======================
# СПИСКИ ПОСТОВ
# ======================

class MainPostListView(ListView):
    model = Post
    template_name = "blog/index.html"
    paginate_by = 10

    def get_queryset(self):
        return get_posts_metadata()


class CategoryPostListView(ListView):
    template_name = "blog/category.html"
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs["category_slug"],
            is_published=True
        )
        return get_posts_metadata(self.category.post_set.all())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["category"] = self.category
        return context


class UserPostsListView(ListView):
    template_name = "blog/profile.html"
    paginate_by = 10

    def get_queryset(self):
        self.author = get_object_or_404(
            User, username=self.kwargs["username"]
        )
        is_author = self.author == self.request.user
        posts = self.author.posts.all()
        return get_posts_metadata(posts, is_author=is_author)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile"] = self.author
        return context


# ======================
# ДЕТАЛЬНЫЙ ПРОСМОТР
# ======================

class PostDetailView(DetailView):
    model = Post
    template_name = "blog/detail.html"

    def get_object(self):
        post = get_object_or_404(
            Post.objects.select_related("category", "author"),
            pk=self.kwargs["pk"]
        )

        if self.request.user != post.author:
            post = get_object_or_404(
                Post,
                pk=post.pk,
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["comments"] = (
            self.object.comments.select_related("author")
        )
        context["form"] = CommentEditForm()
        return context


# ======================
# ПРОФИЛЬ
# ======================

class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = "blog/user.html"

    def get_object(self):
        return self.request.user

    def get_success_url(self):
        return reverse(
            "blog:profile",
            kwargs={"username": self.request.user.username}
        )


# ======================
# ПОСТЫ
# ======================

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostEditForm
    template_name = "blog/create.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "blog:profile",
            kwargs={"username": self.request.user.username}
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostEditForm
    template_name = "blog/create.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            "blog:post_detail",
            kwargs={"pk": self.kwargs["pk"]}
        )


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "blog:profile",
            kwargs={"username": self.request.user.username}
        )


# ======================
# КОММЕНТАРИИ
# ======================

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentEditForm
    template_name = "blog/comment.html"

    def dispatch(self, request, *args, **kwargs):
        self.post = get_post_data(self.kwargs)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.post
        if self.post.author != self.request.user:
            self.send_author_email()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("blog:post_detail", kwargs={"pk": self.post.pk})

    def send_author_email(self):
        send_mail(
            subject="New comment",
            message=f"Новый комментарий к посту {self.post.title}",
            from_email="from@example.com",
            recipient_list=[self.post.author.email],
            fail_silently=True,
        )


class CommentUpdateView(CommentMixinView, UpdateView):
    form_class = CommentEditForm


class CommentDeleteView(CommentMixinView, DeleteView):
    pass
