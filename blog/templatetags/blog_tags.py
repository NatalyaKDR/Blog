import markdown
from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe
from ..models import Post

register = template.Library()


@register.simple_tag  # cоздали простой шаблонный тег, который возвращает число опубликованных в блоге постов
def total_posts():
    return Post.published.count()


@register.inclusion_tag('blog/post/latest_posts.html')  # создадим еще один тег, чтобы отображать последние посты на боковой панели блога. На этот раз мы реализуем тег включения.
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


@register.simple_tag  # создадим тег, чтобы отображать посты с наибольшим числом комментариев.
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('-total_comments')[:count]


# создадим конкретно-прикладной фильтр,
# который позволит использовать синтаксис
# упрощенной разметки Markdown в постах блога, а затем
# в шаблонах конвертировать текст поста в HTML.
@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))
