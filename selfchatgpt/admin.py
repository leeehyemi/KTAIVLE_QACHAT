from django.contrib import admin
from django.core.cache import cache
from .models import chatHistory, User, Profile, faq

admin.site.register(User)
admin.site.register(Profile)

@admin.register(chatHistory) #  chatHistory 모델 관리자 페이지에 등록
class chatHistoryAdmin(admin.ModelAdmin): # 모델 관리를 위해 admin.ModelAdmin 클래스를 상속
    list_display = ('datetime', 'question', 'answer')
    search_fields = ('question', 'answer') # 검색 필터 
    list_filter = ('datetime',) # 기간 필터 적용
    
    def get_queryset(self, request):
        # 캐시 키를 사용하여 쿼리셋을 캐싱
        cache_key = 'chat_history_queryset'
        cached_queryset = cache.get(cache_key)

        if cached_queryset:
            # 캐시된 쿼리셋을 다시 쿼리셋으로 변환
            return chatHistory.objects.filter(id__in=[obj.id for obj in cached_queryset])

        # 쿼리셋 최적화 (필요한 필드만 가져오고, 정렬을 먼저 적용)
        queryset = super().get_queryset(request)
        optimized_queryset = queryset.only('datetime', 'question', 'answer').order_by('-datetime')

        # 상위 20%의 데이터를 슬라이스하여 캐시에 저장
        top_20_percent = list(optimized_queryset[:int(len(optimized_queryset) * 0.2)])
        cache.set(cache_key, top_20_percent, timeout=60 * 5)  # 5분 동안 캐싱

        return optimized_queryset
    

@admin.register(faq) 
class faq(admin.ModelAdmin): 
    list_display = ('answer',)
    search_fields = ('answer',) # 검색 필터 