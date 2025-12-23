# ОТЧЕТ ПО ПРОЕКТУ
# Ахметзянов Арслан, МО02
## «Проект. Приложение „Блогикум“. Часть 3. Доработка»

## 1. Структура проекта Django

Проект реализован с использованием фреймворка Django и имеет стандартную модульную структуру. Основное приложение проекта — `blog`, которое содержит бизнес-логику работы с постами, комментариями, категориями и профилями пользователей.

Структура проекта:

```text
django_sprint4/
├── blogicum/
│   ├── blog/
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── forms.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   ├── views.py
│   │   └── migrations/
│   ├── core/
│   │   ├── mixins.py
│   │   └── utils.py
│   ├── templates/
│   │   └── blog/
│   ├── static/
│   ├── settings.py
│   ├── urls.py
│   └── manage.py
```

Приложение `core` используется для хранения вспомогательной логики, которая переиспользуется в разных частях проекта (миксины, утилиты). Такой подход соответствует принципам DRY и разделения ответственности.

## 2. Модели проекта (models.py)

### Модель Category

Модель категории используется для группировки постов и управления их публикацией.

```python
class Category(models.Model):
    title = models.CharField(max_length=256)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Назначение полей:

* `title` — название категории;
* `slug` — используется в URL;
* `description` — описание категории;
* `is_published` — флаг публикации;
* `created_at` — дата создания.

### Модель Post

Основная модель проекта, представляющая публикацию пользователя.

```python
class Post(models.Model):
    title = models.CharField(max_length=256)
    text = models.TextField()
    pub_date = models.DateTimeField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="posts"
    )
    image = models.ImageField(
        upload_to="posts/",
        blank=True,
        null=True
    )
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

Связи:

* `author` — связь с пользователем;
* `category` — связь с категорией;
* комментарии связаны через `related_name="comments"` в модели `Comment`.

### Модель Comment

Модель комментария к посту.

```python
class Comment(models.Model):
    text = models.TextField()
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="comments"
    )
    created_at = models.DateTimeField(auto_now_add=True)
```

Комментарий всегда привязан к конкретному посту и пользователю.

## 3. Регистрация моделей в админ-панели (admin.py)

Для удобства управления данными модели зарегистрированы в административной панели Django.

```python
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "category",
        "pub_date",
        "is_published",
    )
    list_filter = ("is_published", "category")
    search_fields = ("title", "text")
```

```python
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "is_published")
    prepopulated_fields = {"slug": ("title",)}
```

```python
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("author", "post", "created_at")
```

Админка позволяет:

* модерировать контент;
* управлять публикацией постов и категорий;
* просматривать комментарии.

---

## 4. URL-маршрутизация (urls.py)

Все маршруты приложения `blog` описаны в файле `urls.py`.

```python
app_name = "blog"

urlpatterns = [
    path("", views.MainPostListView.as_view(), name="index"),
    path(
        "category/<slug:category_slug>/",
        views.CategoryPostListView.as_view(),
        name="category_posts",
    ),
    path(
        "profile/<slug:username>/",
        views.UserPostsListView.as_view(),
        name="profile",
    ),
    path(
        "posts/<int:pk>/",
        views.PostDetailView.as_view(),
        name="post_detail",
    ),
    path(
        "edit_profile/",
        views.UserProfileUpdateView.as_view(),
        name="edit_profile",
    ),
    path(
        "posts/create/",
        views.PostCreateView.as_view(),
        name="create_post",
    ),
    path(
        "posts/<int:pk>/edit/",
        views.PostUpdateView.as_view(),
        name="edit_post",
    ),
    path(
        "posts/<int:pk>/delete/",
        views.PostDeleteView.as_view(),
        name="delete_post",
    ),
]
```

Каждый маршрут связан с соответствующим CBV-представлением.

## 5. Представления (views.py): списки постов

### Главная страница

```python
class MainPostListView(ListView):
    model = Post
    template_name = "blog/index.html"
    paginate_by = 10

    def get_queryset(self):
        return get_posts_metadata()
```

Отображает список опубликованных постов с пагинацией.

---

### Посты по категории

```python
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
```

Отображаются только опубликованные посты опубликованной категории.

---

### Профиль пользователя

```python
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
```

Автор страницы видит все свои посты, остальные — только опубликованные.

---

## 6. Детальный просмотр поста

```python
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
```

Для неавтора доступен только опубликованный пост с опубликованной категорией и датой публикации не позднее текущей.

## 7. Формы проекта (forms.py)

Для работы с пользовательским вводом в проекте используются формы Django, основанные на `ModelForm`. Это позволяет автоматически создавать HTML-формы на основе моделей и выполнять валидацию данных.

### Форма редактирования профиля пользователя

```python
class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")
```

Данная форма используется для редактирования профиля текущего пользователя.
Ограничение полей обеспечивает безопасность и предотвращает изменение системных атрибутов пользователя.

### Форма создания и редактирования поста

```python
class PostEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = (
            "title",
            "text",
            "pub_date",
            "category",
            "image",
            "is_published",
        )
```

Форма применяется как при создании нового поста, так и при его редактировании.
Использование одной формы для разных операций снижает дублирование кода.

### Форма комментария

```python
class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
```

Форма предназначена для создания и редактирования комментариев к постам.

## 8. Создание, редактирование и удаление постов

### Создание поста

```python
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
```

Особенности:

* доступ только для авторизованных пользователей;
* автор поста назначается автоматически;
* после создания происходит перенаправление в профиль пользователя.

### Редактирование поста

```python
class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostEditForm
    template_name = "blog/create.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)
```

Редактировать пост может только его автор.
Проверка реализована в методе `dispatch`.

### Удаление поста

```python
class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "blog/create.html"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)
```

Удаление также доступно только автору поста.

## 9. Работа с комментариями

### Создание комментария

```python
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
```

Комментарий привязывается:

* к текущему пользователю;
* к посту, полученному из URL.

### Редактирование и удаление комментариев

```python
class CommentUpdateView(CommentMixinView, UpdateView):
    form_class = CommentEditForm
```

```python
class CommentDeleteView(CommentMixinView, DeleteView):
    pass
```

Общая логика вынесена в миксин `CommentMixinView`.

---

## 10. Использование миксинов (mixins.py)

Миксин для комментариев реализует проверку прав доступа и логику перенаправления.

```python
class CommentMixinView(LoginRequiredMixin, View):
    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_pk"

    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect("blog:post_detail", pk=self.kwargs["pk"])
        get_post_data(self.kwargs)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        pk = self.kwargs["pk"]
        return reverse("blog:post_detail", kwargs={"pk": pk})
```

Миксин:

* проверяет, что пользователь — автор комментария;
* предотвращает доступ к редактированию чужих комментариев;
* обеспечивает единый механизм перенаправления.

## 11. Вспомогательные функции (utils.py)

### Получение данных поста

```python
def get_post_data(kwargs):
    return get_object_or_404(
        Post,
        pk=kwargs.get("pk")
    )
```

Используется при работе с комментариями для получения связанного поста.

### Фильтрация постов

```python
def post_published_query():
    return Post.objects.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )
```

Функция используется для получения только опубликованных постов.

## 12. Отправка email-уведомлений

При добавлении комментария автору поста отправляется email-уведомление.

```python
def send_author_email(self):
    send_mail(
        subject="New comment",
        message=f"Новый комментарий к посту {self.post.title}",
        from_email="from@example.com",
        recipient_list=[self.post.author.email],
        fail_silently=True,
    )
```

Отправка выполняется только в случае, если комментарий оставляет не автор поста.

## Заключение

В ходе выполнения проекта были реализованы:

* полноценная система публикации постов;
* комментарии с ограничением прав доступа;
* профили пользователей;
* административная панель;
* переиспользуемые миксины и утилиты.


