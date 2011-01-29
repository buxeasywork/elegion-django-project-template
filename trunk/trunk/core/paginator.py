from django.core.paginator import *

class CompoundPaginator(Paginator):
    """
    CompoundPaginator -- special paginator that contains two tuples/querysets.
    Very useful, when you need to paginate data from different sources:
     * different qs
     * tuple and qs
    """
    def __init__(self, object_lists, per_page, orphans=0, allow_empty_first_page=True):
        assert len(object_lists) == 2 # TODO support >2 
        
        self.object_lists = object_lists
        self.per_page = per_page
        self.orphans = orphans
        self.allow_empty_first_page = allow_empty_first_page
        self._num_pages = self._count = None

    def _get_object_lists_sublist(self, bottom, top):
        first_list = None
        first_idx = None
        last_list = None
        last_idx = None
        
        for i, list in enumerate(self.object_lists):
            if bottom >= self._counts[i][0] and bottom <= (self._counts[i][1] + self._counts[i][0]):
                first_list = list
                first_idx = i
            if top >= self._counts[i][0] and top <= (self._counts[i][1] + self._counts[i][0]):
                last_list = list
                last_idx = i
                
        assert first_list is not None and last_list is not None
        #assert False, (last_idx, first_idx, self._counts)
        #assert False, enumerate(self.object_lists)[0][1]
        
        if first_idx == last_idx:
            return first_list[bottom - self._counts[first_idx][0]:top - self._counts[first_idx][0]]
        else:
            # this lines convert query set to list (I now it strange, but list() doesn't works)
            len(first_list)
            len(last_list)
            
            part1 = first_list[bottom - self._counts[first_idx][0]:] 
            part2 = last_list[:top - self._counts[last_idx][0]]
            return part1 + part2        
        
    def page(self, number):
        "Returns a Page object for the given 1-based page number."
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        return Page(self._get_object_lists_sublist(bottom, top), number, self)

    def _get_count_one(self, list):
        "Returns the total number of objects, across all pages in one list."        
        try:
            _count = list.count()
        except (AttributeError, TypeError):
            # AttributeError if object_list has no count() method.
            # TypeError if object_list.count() requires arguments
            # (i.e. is of type list).
            _count = len(list)
        return _count
    
    def _get_count(self):
        "Returns the total number of objects, across all pages in all lists."
        if self._count is None:
            self._count = 0
            self._counts = []
            for i, list in enumerate(self.object_lists):
                count = self._get_count_one(list)                
                self._counts.insert(i, (self._count, count))
                self._count += count
        return self._count 
    count = property(_get_count)