# 引入redirect 重定向模块
from django.shortcuts import render, redirect
# 引入HttpResponse
from django.http import HttpResponse
# 引入ArticlePostForm表单类
from .forms import ArticlePostForm
# 引入User模型
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
# 引入分页模块
from django.core.paginator import Paginator

from .models import ArticlePost
import markdown

# 引入 Q 对象
from django.db.models import Q

# Create your views here.
# 文章列表
def article_list(request):
    search = request.GET.get('search')
    order = request.GET.get('order')
    # 用户搜索逻辑
    if search:
        if order == 'total_views':
            # 用 Q 对象进行联合搜索
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) | 
                Q(body__icontains=search)
            ).order_by('-total_views')
        else:
            article_list = ArticlePost.objects.filter(
                Q(title__icontains=search) | 
                Q(body__icontains=search)
            )
    else:
        # 将 search 参数重置为空
        search = ''
        if order == 'total_views':
            article_list = ArticlePost.objects.all().order_by('-total_views')
        else:
            article_list = ArticlePost.objects.all()
    
    # 每页显示 1 篇文章
    paginator = Paginator(article_list, 2)
    # 获取 url 中的页码
    page = request.GET.get('page')
    # 将导航对象相应的页码内容返回给 articles
    articles = paginator.get_page(page)

    # 需要传递给模板的对象
    context = { 'articles': articles, 'order': order, 'search': search }
    return render(request, 'article/list.html', context)

# 文章列表
def article_detail(request, id):
    # 取出相应的文章
    article = ArticlePost.objects.get(id = id)

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
    context = { 'article': article, 'toc': md.toc}
    # 载入模板，并返回context对象
    return render(request, 'article/detail.html', context)

# 写文章
@login_required(login_url='/userprofile/login/')
def article_create(request):
    # 判断用户是否提交数据
    if request.method == 'POST':
        # 将提交的数据赋值给表单实例中
        article_post_form = ArticlePostForm(data=request.POST)
        # 判断提交的数据是否满足模型的要求
        if article_post_form.is_valid():
            # 保存数据，但暂时不提交到数据库中
            new_article = article_post_form.save(commit=False)
            # 指定目前登录的用户为作者
            new_article.author = User.objects.get(id=request.user.id)
            # 将新文章保存在数据库中
            new_article.save()
            # 完成后返回文章列表
            return redirect('article:article_list')
            # 如果数据不合法，返回错误信息
        else:
            return HttpResponse('表单内容有误，请重新填写！')
    # 如果用户请求获取数据
    else:
        # 创建表单类实例
        article_post_form = ArticlePostForm()
        # 赋值上下文
        context = { 'article_post_form': article_post_form }
        # 返回模块
        return render(request, 'article/create.html', context)

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
        # 赋值上下文，将 article 文章对象页传递进去，以便提取旧的内容
        context = { 'article': article, 'article_post_form': article_post_form }
        # 将响应返回到模板中
        return render(request, 'article/update.html', context)