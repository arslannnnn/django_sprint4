from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    # Главная
    path(
        "",
        views.MainPostListView.as_view(),
        name="index",
    ),

    # Категория
    path(
        "category/<slug:category_slug>/",
        views.CategoryPostListView.as_view(),
        name="category_posts",
    ),

    # Профиль пользователя
    path(
        "profile/<str:username>/",
        views.UserPostsListView.as_view(),
        name="profile",
    ),

    # Детальный просмотр поста
    path(
        "posts/<int:post_id>/",
        views.PostDetailView.as_view(),
        name="post_detail",
    ),

    # Редактирование профиля
    path(
        "edit_profile/",
        views.UserProfileUpdateView.as_view(),
        name="edit_profile",
    ),

    # Создание поста
    path(
        "posts/create/",
        views.PostCreateView.as_view(),
        name="create_post",
    ),

    # Редактирование поста
    path(
        "posts/<int:post_id>/edit/",
        views.PostUpdateView.as_view(),
        name="edit_post",
    ),

    # Удаление поста
    path(
        "posts/<int:post_id>/delete/",
        views.PostDeleteView.as_view(),
        name="delete_post",
    ),

    # Добавление комментария
    path(
        "posts/<int:post_id>/comment/",
        views.CommentCreateView.as_view(),
        name="add_comment",
    ),

    # Редактирование комментария
    path(
        "posts/<int:post_id>/edit_comment/<int:comment_id>/",
        views.CommentUpdateView.as_view(),
        name="edit_comment",
    ),

    # Удаление комментария
    path(
        "posts/<int:post_id>/delete_comment/<int:comment_id>/",
        views.CommentDeleteView.as_view(),
        name="delete_comment",
    ),
]
