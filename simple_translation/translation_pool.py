from django.db import models
from django.conf import settings

class TranslationAllreadyRegistered(Exception):
    pass

class TranslationOptions(object):
    """ Options class for info about translated model """
    
    def __init__(self, options={}):
        self.language_field = options.get('language_field', 'language')
        self.translation_of_model = options.get('translation_of_model')
        self.translated_model = options.get('translated_model')
        self.translation_of_field = options.get('translation_of_field')
        self.translations_of_accessor = options.get('translations_of_accessor')
        self.translation_join_filter = options.get('translation_join_filter')
        
class TranslationPool(object):
    """ Pool for registering models with translated model + options """
    
    discovered = False
    translated_models_dict = {}
    translation_models_dict = {}
    
    def discover_translations(self):
        """ Autodiscover simple_translate in all installed apps """
        
        if self.discovered:
            return
        for app in settings.INSTALLED_APPS:
            __import__(app, {}, {}, ['simple_translate'])
        self.discovered = True    

    def get_info(self, model):
        """ Get registered options for translated model or translation of model """

        self.discover_translations()
        if model in self.translated_models_dict:
            return self.translated_models_dict[model]
        elif model in self.translation_models_dict:
            return self.translated_models_dict[ \
                self.translation_models_dict[model]
            ]
        
    def register_translation(self, translation_of_model, translated_model, \
        language_field='language'):
        """ Register a translation of a model and any custom language field in the pool """
        
        assert issubclass(translation_of_model, models.Model) \
            and issubclass(translated_model, models.Model)
        
        if translation_of_model in self.translated_models_dict:
            raise TranslationAllreadyRegistered, \
                "[%s] a translation for this model is already registered" \
                    % translation_of_model.__name__
            
        options = {}    
        options['translated_model'] = translated_model
        
        opts = translation_of_model._meta
        for rel in opts.get_all_related_objects():
            if rel.model == translated_model:
                options['translation_of_field'] = rel.field.name
                options['translations_of_accessor'] = rel.get_accessor_name()

        options['translation_join_filter'] = translated_model.__name__.lower()          
        options['language_field'] = language_field     
        
        self.translated_models_dict[translation_of_model] = TranslationOptions(options)
        # keep track both ways
        self.translation_models_dict[translated_model] = translation_of_model

    def unregister_translation(self, translation_of_model):
        """ Unregister a translated model from the pool """
        info = self.get_info(translation_of_model)
        del self.translation_models_dict[info.translated_model]
        del self.translated_models_dict[translation_of_model]

    def is_registered_translation(self, model):
        """ Check if a translation model is registered in the pool """
        self.discover_translations()
        if model in self.translation_models_dict:
            return True
        return False
        
    def is_registered(self, model):
        """ Check if a translated model is registered in the pool """
        self.discover_translations()
        if model in self.translated_models_dict:
            return True
        return False
            
translation_pool = TranslationPool()
