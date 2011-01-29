from django.core.management.base import LabelCommand
from django.core.serializers import serialize


class Command(LabelCommand):
    help = """ Export to json, models or entire models modules """
    args = '<model1 models_module model2 ...>'
    label = 'model'

    def get_mod_func(self, callback):
        # Converts 'django.views.news.stories.story_detail' to
        # ['django.views.news.stories', 'story_detail']
        try:
            dot = callback.rindex('.')
        except ValueError:
            return callback, ''
        return callback[:dot], callback[dot+1:]

    def write_model(self, file, cls):
        for obj in cls.objects.all():
            file.write(serialize('json', [obj])[1:-1])
            file.write(',\n')

    def handle_label(self, label, **options):
        module, cls_name = self.get_mod_func(label)
        try:
            cls = getattr(__import__(module, {}, {}, ['']), cls_name)
            filename = cls.__name__.lower() + '.json'
            file = open(filename, 'w')
            self.write_model(file, cls)
        except AttributeError:
            #parse all models
            module = __import__(label, {}, {}, [''])
            filename = module.__name__.lower() + '.json'
            file = open(filename, 'w')
            for model_name in dir(module):
                model = getattr(module, model_name)
                if hasattr(model, 'objects'):
                    self.write_model(file, model)
                    file.write('\n')

