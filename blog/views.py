from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from taggit.models import Tag

from .forms import EmailPostForm, CommentForm
from .models import Post


def post_list(request, tag_slug=None):
    post_list = Post.published.all()

    # Теги
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        post_list = post_list.filter(tags__in=[tag])

    # Постраничная разбивка с 3 постами на страницу
    paginator = Paginator(post_list, 3)
    page_number = request.GET.get('page', 1)
    # try:
    #     posts = paginator.page(page_number)
    # except PageNotAnInteger:
    #     # Если page_number не целое число, то
    #     # выдать первую страницу
    #     posts = paginator.page(1)
    # except EmptyPage:
    #     # Если page_number находится вне диапазона, то
    #     # выдать последнюю страницу результатов
    #     posts = paginator.page(paginator.num_pages)
    posts = paginator.get_page(page_number)  # try except можно заменить методом get_page
    return render(request, 'blog/post/list.html', {'posts': posts, 'tag':tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)
    # Форма для комментирования пользователями
    form = CommentForm()

    # Список схожих постов
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]

    return render(request,'blog/post/detail.html',{'post': post,'comments': comments, 'form': form, 'similar_posts': similar_posts})


class PostListView(ListView):
    """
    Альтернативное представление списка постов
    """
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 3
    template_name = 'blog/post/list.html'


def post_share(request, post_id):
    # Извлечь пост по идентификатору id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    sent = False
    if request.method == 'POST':  # Форма была передана на обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():  # Поля формы успешно прошли валидацию
            # ... отправить электронное письмо
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(
                post.get_absolute_url())  # чтобы сформировать полный URL-адрес, включая HTTP-схему и хост-имя (hostname)
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'kanstantsinliskovich@gmail.com', [cd['to']])

            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})

@require_POST
# используем предоставляемый веб-фреймворком Django декоратор require_POST,
# чтобы разрешить запросы методом POST только для этого представления
# Если пытаться обращаться к представлению посредством любого другого
# HTTP-метода, то Django будет выдавать ошибку HTTP 405 (Метод не разрешен)
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)
    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса Comment, не сохраняя его в базе данных
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий в базе данных
        comment.save()
    return render(request, 'blog/post/comment.html', {'post': post, 'form': form, 'comment':comment})