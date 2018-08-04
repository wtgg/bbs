'''
用户
 ^
 |  多对多
 v
角色
 ^
 |  多对多
 v
权限


权限分配状况

xyz
    user: 'add_post'
        : 'add_comment'

abc
    manager: 'add_post'
           : 'add_comment'
           : 'del_post'
           : 'del_comment'

dev
    admin: 'del_comment'
         : 'del_post'
         : 'del_user'
'''

from django.db import models


class User(models.Model):
    SEX = (
        ('M', '男性'),
        ('F', '女性'),
        ('U', '保密'),
    )
    nickname = models.CharField(max_length=32, unique=True)
    password = models.CharField(max_length=128)
    icon = models.ImageField()
    plt_icon = models.CharField(max_length=256, default='')
    age = models.IntegerField(default=18)
    sex = models.CharField(max_length=8, choices=SEX)

    @property
    def avatar(self):
        if self.icon:
            return self.icon.url
        else:
            return self.plt_icon

    def roles(self):
        '''用户绑定的所有角色'''
        relations = UserRoleRelation.objects.filter(uid=self.id).only('role_id')
        role_id_list = [r.role_id for r in relations]
        return Role.objects.filter(id__in=role_id_list)

    def has_perm(self, perm_name):
        '''检查用户是否具有某权限'''
        for role in self.roles():
            for perm in role.perms():
                if perm.name == perm_name:
                    return True
        return False


class UserRoleRelation(models.Model):
    uid = models.IntegerField()
    role_id = models.IntegerField()

    @classmethod
    def add_role_to_user(cls, uid, role_name):
        '''给用户添加一个角色'''
        role = Role.objects.get(name=role_name)
        relation, _ = cls.objects.get_or_create(uid=uid, role_id=role.id)
        return relation

    @classmethod
    def del_role_from_user(cls, uid, role_name):
        '''删除用户的某个角色'''
        role = Role.objects.get(name=role_name)
        cls.objects.get(uid=uid, role_id=role.id).delete()


class Role(models.Model):
    '''
    角色表
        admin   管理员
        manager 版主
        user    普通用户
    '''
    name = models.CharField(max_length=16, unique=True)

    def perms(self):
        '''角色绑定的所有权限'''
        relations = RolePermRelation.objects.filter(role_id=self.id).only('perm_id')
        perm_id_list = [r.perm_id for r in relations]
        return Permission.objects.filter(id__in=perm_id_list)


class RolePermRelation(models.Model):
    role_id = models.IntegerField()
    perm_id = models.IntegerField()

    @classmethod
    def add_perm_to_role(cls, role_id, perm_name):
        '''给角色添加某个权限'''
        perm = Permission.objects.get(name=perm_name)
        relation, _ = cls.objects.get_or_create(role_id=role_id, perm_id=perm.id)
        return relation

    @classmethod
    def del_perm_from_role(cls, role_id, perm_name):
        '''删除角色的某个权限'''
        perm = Permission.objects.get(name=perm_name)
        cls.objects.get(role_id=role_id, perm_id=perm.id).delete()

class Permission(models.Model):
    '''
    权限表
        add_post    添加帖子权限
        del_post    删除帖子权限
        add_comment 添加评论权限
        del_comment 删除评论权限
        del_user    删除用户权限
    '''
    name = models.CharField(max_length=16, unique=True)
