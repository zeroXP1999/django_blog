from django.db.models import Q
from django.http import HttpResponse
from django.views.generic import ListView, View
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

import markdown

from .models import ArticlePost, ArticleColumn
from comment.models import Comment
from .forms import ArticlePostForm
from comment.forms import CommentForm



# 文章列表
def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    column = request.GET.get('column')
    tag = request.GET.get('tag')

    # 初始化查询集
    article_list = ArticlePost.objects.all()

    # 用户搜索逻辑
    if search:
        article_list = ArticlePost.objects.filter(
            Q(title__icontains=search) | 
            Q(body__icontains=search)
        )
    else:
        search = ''
    
    # 栏目查询集
    if column is not None and column.isdigit():
        article_list = article_list.filter(column=column)
    else:
        column = ''
    
    # 标签查询集
    if tag and tag != 'None':
        article_list = article_list.filter(tags__name__in=[tag])
    else:
        tag = ''

    # 查询集排序
    if order == 'total_views':
        article_list = article_list.order_by('-total_views')
    else:
        order = ''
        

    # 每页显示 1 篇文章
    paginator = Paginator(article_list, 3)
    # 获取 url 中的页码
    page = request.GET.get('page')
    # 将导航对象相应的页码内容返回给 articles
    articles = paginator.get_page(page)

    # 需要传递给模板的对象
    context = { 'articles': articles, 'order': order, 'search': search, 'column': column, 'tag': tag, }
    return render(request, 'article/list.html', context)

# 写文章
@login_required(login_url='/userprofile/login/')
def article_create(request):
    # 判断用户是否提交数据
    if request.method == 'POST':
        # 将提交的数据赋值给表单实例中
        article_post_form = ArticlePostForm(request.POST, request.FILES)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            if request.POST['column'] != 'none':
                new_article.column = ArticleColumn.objects.get(id=request.POST['column'])
            # 将新文章保存在数据库中
            new_article.save()

            # 保存 tags 的多对多关系
            article_post_form.save_m2m()
            # 完成后返回文章列表
            return redirect('article:article_list')
            # 如果数据不合法，返回错误信息
        else:
            
            return HttpResponse('表单内容有误，请重新填写！')
    # 如果用户请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = { 'article_post_form': article_post_form, 'columns': columns }
        # 返回模块
        return render(request, 'article/create.html', context)


# 文章详情
def article_detail(request, id):
    # 取出相应的文章
    article = ArticlePost.objects.get(id = id)

    # 过滤出所有id比当前文章小的文章
    pre_article = ArticlePost.objects.filter(id__lt=article.id).order_by('-id')
    # 过滤出所有id比当前文章大得文章
    next_article = ArticlePost.objects.filter(id__gt=article.id).order_by('id')
     # 取出相邻前一篇文章
    if pre_article.count() > 0:
        pre_article = pre_article[0]
    else:
        pre_article = None

    # 取出相邻后一篇文章
    if next_article.count() > 0:
        next_article = next_article[0]
    else:
        next_article = None

    # 引入评论表单
    comment_form = CommentForm()

    # 取出文章评论
    comments = Comment.objects.filter(article=id)

    # 浏览量 + 1
    article.total_views += 1
    article.save(update_fields=['total_views'])
    # 需要传递给模板的对象
    # 将markdown 语法渲染成html样式
    md = markdown.Markdown(extensions = [
        # 包含 缩写、表格等常用拓展
        'markdown.extensions.extra',
        # 语法高亮拓展
        'markdown.extensions.codehilite',
        # 目录拓展
        'markdown.extensions.toc'
    ])
    article.body = md.convert(article.body)
    context = {
        'article': article,
        'toc': md.toc,
        'comments': comments,
        'comment_form': comment_form,
        'pre_article': pre_article,
        'next_article': next_article, }
    # 载入模板，并返回context对象
    return render(request, 'article/detail.html', context)

# 更新文章
@login_required(login_url='/userprofile/login/')
def article_update(request, id):
    # 获取需要修改的具体文章对象
    article = ArticlePost.objects.get(id=id)

    if request.user != article.author:
        return HttpResponse('抱歉，你无权修改这篇文章！')
    # 判断用户是否为 POST 提交表单数据
    if request.method == 'POST':
        # 将提交的数据赋值到表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保持新写入的 title、body 数据并保存
            article.title = request.POST['title']
            article.body = request.POST['body']
            if request.POST['column'] != 'none':
                article.column = ArticleColumn.objects.get(id=request.POST['column'])
            else:
                article.column = None
            
            article.save()
            # 完成后返回到修改后的文章中，需传入文章的 id 值
            return redirect('article:article_detail', id=id)
        # 如果数据不合法，返回错误信息
        else: 
            return HttpResponse('表单内容有误，请重新填写！')
    # 如果用户 GET 请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        columns = ArticleColumn.objects.all()
        context = { 'article': article, 'article_post_form': article_post_form, 'columns': columns }
        # 将响应返回到模板中
        return render(request, 'article/update.html', context)

# 删除文章
@login_required(login_url='/userprofile/login/')
def article_safe_delete(request, id):
    if request.method == 'POST':
        # 根据 id 获取需要删除的文章
        article = ArticlePost.objects.get(id=id)
        if request.user != article.author:
            return HttpResponse('抱歉，你无权修改这篇文章！')
        # 调用 .delete() 方法删除文章
        article.delete()
        # 完成删除后返回文章列表
        return redirect('article:article_list')
    else:
        return HttpResponse('仅允许post请求')


class ContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['order'] = 'total_views'
        return context

class ArticleListView(ContextMixin, ListView):
    context_object_name = 'articles'
    template_name = 'article/list.html'
    
    def get_queryset(self):
        search = self.request.GET.get('search')
        order = self.request.GET.get('order')
        if search:
            if order == 'total_views':
                # 用 Q 对象进行联合搜索
                queryset = ArticlePost.objects.filter(
                    Q(title__icontains=search) | 
                    Q(body__icontains=search)
                ).order_by('-total_views')
            else:
                queryset = ArticlePost.objects.filter(
                    Q(title__icontains=search) | 
                    Q(body__icontains=search)
                )
        else:
            # 将 search 参数重置为空
            search = ''
            if order == 'total_views':
                queryset = ArticlePost.objects.all().order_by('-total_views')
            else:
                queryset = ArticlePost.objects.all()
        return queryset

# 点赞数
class IncreaseLikeView(View):
    def post(self, request, *args, **kwargs):
        article = ArticlePost.objects.get(id=kwargs.get('id'))
        article.likes += 1
        article.save()
        return HttpResponse('success')
