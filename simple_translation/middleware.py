from django.conf import settings
from django.utils import translation
from django.middleware.locale import LocaleMiddleware

from simple_translation.utils import filter_queryset_language

class MultilingualGenericsMiddleware(LocaleMiddleware):
    
    language_fallback_middlewares = ['django.middleware.locale.LocaleMiddleware']
    
    def has_language_fallback_middlewares(self):
        has_fallback = False
        for middleware in self.language_fallback_middlewares: 
            if middleware in settings.MIDDLEWARE_CLASSES:
                has_fallback = True
        return has_fallback
        
    def process_request(self, request):
        pass
        
    def process_view(self, request, view_func, view_args, view_kwargs):
        language = None
        if 'language_code' in view_kwargs:
            # get language and set tralslation
            language = view_kwargs.pop('language_code')
            translation.activate(language)
            request.LANGUAGE_CODE = translation.get_language()

        if 'queryset' in view_kwargs:
            view_kwargs['queryset'] = filter_queryset_language(request, view_kwargs['queryset'])  

    def process_response(self, request, response):
        if not self.has_language_fallback_middlewares():
            return super(MultilingualGenericsMiddleware, self).process_response(request, response)
        return response
