from django.conf import settings
from django.middleware.locale import LocaleMiddleware
from django.utils import translation

from simple_translation.translation_pool import translation_pool

def filter_queryset_language_code(request, queryset, language):
    model = queryset.model
    filter_expr = None
    if translation_pool.is_registered(model):
        info = translation_pool.get_info(model)
        filter_expr = '%s__%s' % (info.translation_join_filter, info.language_field)
    if translation_pool.is_registered_translation(model):
        info = translation_pool.get_info(model)
        filter_expr = '%s' % info.language_field
    if filter_expr:
        queryset = queryset.filter( \
            **{filter_expr: language}).distinct()            
    return queryset
    
def filter_queryset_language(request, queryset):
    language = getattr(request, 'LANGUAGE_CODE')
    return filter_queryset_language_code(request, queryset, language)
    
class BaseMultilingualMiddleware(LocaleMiddleware):
    
    is_generic_middleware = False
    language_fallback_middlewares = ['django.middleware.locale.LocaleMiddleware']
 
    def has_language_fallback_middlewares(self):
        has_fallback = False
        for middleware in self.language_fallback_middlewares: 
            if middleware in settings.MIDDLEWARE_CLASSES:
                has_fallback = True
        return has_fallback

    def process_response(self, request, response):
        if not self.has_language_fallback_middlewares():
            return super(MultilingualGenericsMiddleware, self).process_response(request, response)
        return response
        
class FilterQuerysetMixin(object):
    """ Filters any queryset passed to the view based on request.LANGUAGE_CODE """
    
    is_generic_middleware = True
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        if 'queryset' in view_kwargs:
            view_kwargs['queryset'] = filter_queryset_language(request, view_kwargs['queryset'])  

class MultilingualUrlMixin(object):
    """ Checks for language_code and in view_kwargs, sets language, call super depending on is_generic_middleware """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        language = None
        if 'language_code' in view_kwargs:
            # get language and set tralslation
            language = view_kwargs.pop('language_code')
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()
            
        if self.is_generic_middleware:
            super(MultilingualUrlMixin, self).process_view(request, view_func, view_args, view_kwargs):
            
class MultilingualUrlMiddleware(BaseMultilingualMiddleware, MultilingualUrlMixin):
    """ Checks for language_code and in view_kwargs, sets language """
    pass
    
class MultilingualNoUrlGenericsMiddleware(BaseMultilingualMiddleware, FilterQuerysetMixin):
    """ Filters any queryset passed to the view based on request.LANGUAGE_CODE """
    pass
    
class CmsMultilingualGenericsMiddleware(MultilingualNoUrlGenericsMiddleware):
    """ Filters any queryset passed to the view based on request.LANGUAGE_CODE tests for django-cms middleware"""
    
    language_fallback_middlewares = [
        'django.middleware.locale.LocaleMiddleware',
        'cms.middleware.multilingual.MultilingualURLMiddleware'
    ]

class MultilingualUrlGenericsMiddleware(MultilingualGenericsMiddleware, MultilingualUrlMixin):
    """ Checks for language_code in view_kwargs, sets language and filters any queryset passed to the view by request.LANGUAGE_CODE """
    pass

class MultilingualGenericsMiddleware(MultilingualUrlGenericsMiddleware):
    """ For backwards compatibility """
    pass