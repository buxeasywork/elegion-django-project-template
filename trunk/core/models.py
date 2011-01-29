# -*- coding: UTF-8 -*-
from django.forms.models import ModelChoiceIterator
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from core.auth.models import LoginAttempt
from core.signals import post_mark_deleted, post_unmark_deleted


class FilteredModelChoiceIterator(ModelChoiceIterator):
    """
    Hacked django's ModelChoiceIterator.
    Adds in choices list field, containing id of foreign key.
    Used by core.fields.FilteredSelectField.

    """
    def __init__(self, field):
        super(FilteredModelChoiceIterator, self).__init__(field)

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u'', self.field.empty_label, u'')

        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    self.choice(obj) for obj in self.queryset.all()
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for obj in self.queryset.all():
                yield self.choice(obj)

    def choice(self, obj):
        if self.field.to_field_name:
            # FIXME: The try..except shouldn't be necessary here. But this is
            # going in just before 1.0, so I want to be careful. Will check it
            # out later.
            try:
                key = getattr(obj, self.field.to_field_name).pk
            except AttributeError:
                key = getattr(obj, self.field.to_field_name)
        else:
            key = obj.pk
        filter_key = '0'
        if hasattr(obj, self.field.foreign_key):
            filter_key = getattr(obj, self.field.foreign_key)
        return (key, self.field.label_from_instance(obj), filter_key)


class DirtyFieldsMixin(object):
    def __init__(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).__init__(*args, **kwargs)
        self._original_state = self._as_dict()

    def _as_dict(self):
        res = []
        for f in self._meta.local_fields:
            if isinstance(f, models.ForeignKey):
                res.append((f.name, getattr(self, f.name + '_id')))
            else:
                res.append((f.name, getattr(self, f.name)))
        return dict(res)
    
    def get_dirty_fields(self):
        """ Returns fields modified since last save() / __init__()
        """
        new_state = self._as_dict()
        return dict([(key, value) for key, value in self._original_state.iteritems() if value != new_state[key]])

    def save(self, *args, **kwargs):
        super(DirtyFieldsMixin, self).save(*args, **kwargs)
        self._original_state = self._as_dict()


class MarkDeletedSignalsModel(DirtyFieldsMixin):
    
    def save(self, *args, **kwargs):
        insert = (self.pk == None)
        changed_cols = self.get_dirty_fields()
        
        super(MarkDeletedSignalsModel, self).save(*args, **kwargs)
        
        if not insert and changed_cols.has_key('deleted_by'):
            if self.deleted_by:
                post_mark_deleted.send(sender=self.__class__, instance=self)
            else:
                post_unmark_deleted.send(sender=self.__class__, instance=self)
