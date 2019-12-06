from django.db import models

from django.contrib.auth.models import User

from django.utils import timezone

from django.urls import reverse
# Create your models here.

# 博客文章数据类型模型
class ArticlePost(models.Model):
    # 文章作者
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    # 文章标题
    title = models.CharField(max_length=100)

    # 文章正文
    body = models.TextField()

    # 文章创建时间
    created = models.DateTimeField(default=timezone.now)

    # 文章更新时间
    updated = models.DateTimeField(auto_now=True)

    # 文章浏览量
    total_views = models.PositiveIntegerField(default=0)

    # 内部类 class Meta 用于给 model 定义元数据
    class Meta:
        ordering = ('-created',)

    # 函数 __str__ 定义当调用对象的 str() 方法时的返回值内容
    def __str__(self):
        return self.title

    # 获取文章地址
    def get_absolute_url(self):
        return reverse('article:article_detail', args=[self.id])
