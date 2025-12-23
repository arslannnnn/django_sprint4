from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View

from blog.models import Comment, Post


class CommentMixinView(LoginRequiredMixin, View):
    """Mixin для редактирования и удаления комментария."""

    model = Comment
    template_name = "blog/comment.html"
    pk_url_kwarg = "comment_id"

    def dispatch(self, request, *args, **kwargs):
        comment = get_object_or_404(
            Comment,
            pk=self.kwargs["comment_id"]
        )

        if comment.author != request.user:
            return redirect(
                "blog:post_detail",
                post_id=self.kwargs["post_id"]
            )

        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        return get_object_or_404(
            Comment,
            pk=self.kwargs["comment_id"]
        )

    def get_success_url(self):
        return reverse(
            "blog:post_detail",
            kwargs={"post_id": self.kwargs["post_id"]}
        )
