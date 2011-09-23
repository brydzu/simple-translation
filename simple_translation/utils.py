from django.conf import settings
from simple_translation.translation_pool import translation_pool

def get_language_from_request(request):
    return request.REQUEST.get('language', getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE))
    
def annotate_with_translations(list_or_instance):
    """ Annotate object or each object in a list with available translations """
    
    if not list_or_instance:
        return list_or_instance
    languages = [language_code for language_code, language_name in settings.LANGUAGES]
    
    model = list_or_instance.__class__ if isinstance(
        list_or_instance, models.Model
    ) else list_or_instance[0].__class__
    info = translation_pool.get_info(model)

    # Helper function that sorts translations according to settings.LANGUAGES
    def language_key(translation):
        l = getattr(translation, info.language_field)
        try:
            return languages.index(l)
        except ValueError:
            pass

    if isinstance(list_or_instance, models.Model):
        instance = list_or_instance
        if translation_pool.is_registered_translation(model):
            instance = getattr(list_or_instance, \
                info.translation_of_field)
        
        translations = list(getattr(instance, \
        	info.translations_of_accessor).filter(**{'%s__in' % info.language_field: languages}))

        list_or_instance.translations = sorted(translations, key=language_key)
        
        return list_or_instance
    else:
        result_list = list_or_instance
        if not len(result_list):
            return result_list
                        
        id_list = [r.pk for r in result_list]
        pk_index_map = dict([(pk, index) for index, pk in enumerate(id_list)])
        
        translations = info.translated_model.objects.filter(**{
            info.translation_of_field + '__in': id_list,
            info.language_field + '__in': languages,
        })
        
        new_result_list = []
        for obj in translations:
            index = pk_index_map[getattr(obj, info.translation_of_field + '_id')]
            if not hasattr(result_list[index], 'translations'):
                result_list[index].translations = []
            result_list[index].translations.append(obj)
        
        for result in result_list:
            result.translations = sorted(result.translations, key=language_key)
           
    return result_list
    
def filter_queryset_language(request, queryset):
    """ Filter objects having a translation in the current language """

    language = getattr(request, 'LANGUAGE_CODE', None)

    if not language:
        return queryset

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
    
def get_preferred_translation_from_request(obj, request):
    """ Get translated object in the current language """
    language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
    if not hasattr(obj, 'translations'):
        annotate_with_translations(obj)
    for translation in obj.translations:
        if translation.language == language:
            return translation
    return obj.translations[0]
    
def get_preferred_translation_from_lang(obj, language):
    """ Get translated object in the language specified """
    if not hasattr(obj, 'translations'):
        annotate_with_translations(obj)
    for translation in obj.translations:
        if translation.language == language:
            return translation
    return obj.translations[0]
    
def get_translation_of_field(model):
    """ Get the foreignkey field name from translation model to translated model i.e. 'entry' """
    return translation_pool.get_info(model).translation_of_field
    
def get_language_field(model):
    """ Get the language field name for translaton model for model i.e. 'language' """
    return translation_pool.get_info(model).language_field
        
def get_translation_filter_field(model, field):
    """ Get the join string for the field specified field on translation model i.e. 'entrytitle__field' """
    info = translation_pool.get_info(model)
    join_filter = info.translation_join_filter
    return '%s__%s' % (join_filter, field)
        
def get_translation_filter_fields(model, fields):
    """ 
    Get the join string for the fields specified on translation model
    
    i.e.
     
    get_translation_filter_fields(Entry, [ 'field', 'field2' ])
    
    Gives ['entrytitle__field', 'entrytitle__field2']
    
    """
    for field in fields:
        yield get_translation_filter_field(model, field)
   
def get_translation_filter(model, **kwargs):
    """
    Get a dict with each key in kwargs replaced with the join string for a field on translation model
    
    i.e. 
    
    get_translation_filter(Entry, {
        'field': 'value',
        'field2': 'value2'
    })
    
    Gives
    
    {
        'entrytitle__field': 'value',
        'entrytitle__field2': 'value2'
    }
    """
    filter_dict = {}
    for key, value in kwargs.items():
        filter_dict[get_translation_filter_field(model, key)] = value
    return filter_dict
     
def get_translation_filter_language(model, language, **kwargs):
    """ Get a dict with each key in kwargs replaced with the join string for a field on translation model
    
    i.e. 
    
    get_translation_filter(Entry, 'en', {
        'field': 'value',
        'field2': 'value2'
    })
    
    Gives
    
    {   'entrytitle__language': 'en',
        'entrytitle__field': 'value',
        'entrytitle__field2': 'value2'
    }
    """
    info = translation_pool.get_info(model)
    kwargs[info.language_field] = language
    return get_translation_filter(model, **kwargs)

def get_translation_manager(obj):
    """ Get the manager to get at translations fom the object i.e. object.entrytitle_set """
    info = translation_pool.get_info(obj.__class__)
    return getattr(obj, info.translations_of_accessor)

def get_translation_queryset(obj):
    """ Get the queryset to get at translations fom the object i.e. object.entrytitle_set.all() """
    return get_translation_manager(obj).all()  

def get_translated_model(model):
    """ Get the translation model for model i.e. EntryTitle for Entry """
    return translation_pool.get_info(model).translated_model
