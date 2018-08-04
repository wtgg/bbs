# coding: utf-8

from django.core.cache import cache

from common import rds
from post.models import Post

'''
更新策略
    主动更新
    主动删除
    过期时间
'''

def page_cache(timeout):
    def wrapper1(view_func):
        def wrapper2(request):
            key = 'PageCache-%s-%s' % (request.session.session_key, request.get_full_path())
            response = cache.get(key)
            print('Get from cache', response)
            if response is None:
                response = view_func(request)
                print('Get from view', response)
                cache.set(key, response, timeout)
                print('Set to cache')
            return response
        return wrapper2
    return wrapper1


def read_count(read_view):
    def wrapper(request):
        response = read_view(request)
        if response.status_code == 200:
            post_id = int(request.GET.get('post_id'))
            rds.zincrby('ReadRank', post_id)
        return response
    return wrapper


def get_top_n(num):
    '''获取排名数据'''
    # ori_data = [
    #     (b'33', 843.0),
    #     ( b'1', 384.0),
    #     (b'29', 261.0),
    # ]
    ori_data = rds.zrevrange('ReadRank', 0, num - 1, withscores=True)  # 取出原始排名数据

    # cleaned_data = [
    #     [33, 1779],
    #     [ 1,  384],
    #     [29,  261],
    # ]
    cleaned_data = [[int(post_id), int(count)] for post_id, count in ori_data]  # 数据清洗

    # 方法一
    # for item in cleaned_data:
    #     item[0] = Post.objects.get(id=item[0])
    # rank_data = cleaned_data

    # 方法二
    # post_id_list = [post_id for post_id, _ in cleaned_data]
    # posts = Post.objects.filter(id__in=post_id_list)  # 批量取出 posts
    # posts = sorted(posts, key=lambda post: post_id_list.index(post.id))  # 按照id的索引进行排序
    # # 拼装 rank_data
    # rank_data = []
    # for post, (_, count) in zip(posts, cleaned_data):
    #     rank_data.append([post, count])

    # 方法三
    post_id_list = [post_id for post_id, _ in cleaned_data]
    # post_dict = {
    #     1: <Post: Post object>,
    #     2: <Post: Post object>,
    #     3: <Post: Post object>,
    # }
    post_dict = Post.objects.in_bulk(post_id_list)
    for item in cleaned_data:
        item[0] = post_dict[item[0]]
    rank_data = cleaned_data

    return rank_data
