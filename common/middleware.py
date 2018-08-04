# coding: utf-8

import time

from django.core.cache import cache
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin


def simple_middleware(view):
    def middleware(request):
        print('----------------> process_request')
        response = view(request)
        print('----------------> process_response')
        return response
    return middleware


class BlockMiddleware(MiddlewareMixin):
    '''
    最大每秒 3 次

        1. 1533116000.00
        2. 1533116000.33
        ------------------
        3. 1533116000.51
        4. 1533116001.87
        5. 1533116002.99
        ------------------
        6. 1533116003.21
        ------------------
        7. 1533116004.39
    '''
    def process_request(self, request):
        user_ip = request.META['REMOTE_ADDR']
        request_key = 'RequestLog-%s' % user_ip
        block_key = 'Block-%s' % user_ip

        # 检查黑名单
        if cache.get(block_key):
            return render(request, 'blockers.html')

        now = time.time()
        t0, t1, t2 = cache.get(request_key, [0, 0, 0])
        # 检查访问频率
        if (now - t0) < 1:
            cache.set(block_key, 1, 15)
        else:
            # 更新访问时间
            cache.set(request_key, [t1, t2, now])
