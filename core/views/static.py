from django.views import static


def serve(request, path, document_root=None, show_indexes=False):
    # To allow setup firefox addon on dev server
    import mimetypes
    mimetypes.add_type('application/x-xpinstall', '.xpi')
    mimetypes.add_type('application/rdf+xml', '.rdf')
    mimetypes.add_type("application/msi", ".msi")
    return static.serve(request, path, document_root, show_indexes)

