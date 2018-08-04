from django.db import models

from user.models import User


class Post(models.Model):
    uid = models.IntegerField()
    title = models.CharField(max_length=64)
    created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    @property
    def auth(self):
        if not hasattr(self, '_auth'):
            self._auth = User.objects.get(id=self.uid)
        return self._auth

    def comments(self):
        return Comment.objects.filter(post_id=self.id).order_by('-id')

    def tags(self):
        relations = PostTagRelation.objects.filter(post_id=self.id).only('tag_id')
        tag_id_list = [r.tag_id for r in relations]
        return Tag.objects.filter(id__in=tag_id_list)

    def update_tags(self, tag_names):
        '''更新当前 Post 的 tag'''
        Tag.ensure_exist(tag_names)  # 确保传入的 name 是存在的

        update_names = set(tag_names)                # 需要全新建立关联的 name
        exist_names ={t.name for t in  self.tags()}  # 已存在关联的 name

        # 筛选待创建的关系
        need_create_names = update_names - exist_names
        PostTagRelation.add_post_tags(self.id, need_create_names)

        # 筛选出需要删除的关系
        need_delete_names = exist_names - update_names
        PostTagRelation.del_post_tags(self.id, need_delete_names)


class Comment(models.Model):
    uid = models.IntegerField()
    post_id = models.IntegerField()
    created = models.DateTimeField(auto_now_add=True)
    content = models.TextField()

    @property
    def auth(self):
        if not hasattr(self, '_auth'):
            self._auth = User.objects.get(id=self.uid)
        return self._auth

    @property
    def post(self):
        if not hasattr(self, '_post'):
            self._post = Post.objects.get(id=self.post_id)
        return self._post


class Tag(models.Model):
    name = models.CharField(max_length=16, unique=True)

    @classmethod
    def ensure_exist(cls, names):
        '''确保tag已存在'''
        exist_names = {t.name for t in cls.objects.filter(name__in=names)}  # 取出已存在的 tag name
        new_names = set(names) - exist_names               # 筛选出未创建过的 name
        new_tags = [cls(name=name) for name in new_names]  # 产生出待创建的 tag 对象
        cls.objects.bulk_create(new_tags)                  # 批量创建

    def posts(self):
        relations = PostTagRelation.objects.filter(tag_id=self.id).only('post_id')
        post_id_list = [r.post_id for r in relations]
        return Post.objects.filter(id__in=post_id_list)


class PostTagRelation(models.Model):
    '''
    Post 与 Tag 的关系表

        Django部署   django
        Django部署   python
        Django部署   linux
        Linux对比    linux
        Linux对比    python
        nginx       django
        nginx       linux
    '''
    post_id = models.IntegerField()
    tag_id = models.IntegerField()

    @classmethod
    def add_post_tags(cls, post_id, tag_names):
        '''批量添加 post 与 tag 的关系'''
        tags = Tag.objects.filter(name__in=tag_names).only('id')           # 取出传入的 tags
        new_relations = [cls(post_id=post_id, tag_id=t.id) for t in tags]  # 生成待创建的关系对象
        cls.objects.bulk_create(new_relations)                             # 批量创建

    @classmethod
    def del_post_tags(cls, post_id, tag_names):
        '''批量删除 post 与 tag 的关系'''
        tags = Tag.objects.filter(name__in=tag_names).only('id')  # 取出传入的 tags
        tag_id_list = [t.id for t in tags]                        # 生成待删除的 tag id 列表
        cls.objects.filter(post_id=post_id, tag_id__in=tag_id_list).delete()  # 筛选、删除
