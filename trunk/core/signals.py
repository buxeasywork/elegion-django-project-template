from django.dispatch import Signal


post_mark_deleted = Signal(providing_args=["instance"])

post_unmark_deleted = Signal(providing_args=["instance"])
