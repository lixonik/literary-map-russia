from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.shortcuts import get_object_or_404, render

from .media import open_or_404, ranged_file_response
from .models import Author, Grade, Material


def home(request):
    authors = list(Author.objects.prefetch_related('grades'))
    map_authors = [author for author in authors if author.on_map]
    context = {
        'authors': authors,
        'map_authors': map_authors,
        'map_regions_count': len({author.region for author in map_authors}),
        'grades': Grade.objects.all(),
    }
    return render(request, 'literature/home.html', context)


def author_detail(request, slug):
    author = get_object_or_404(
        Author.objects.prefetch_related('works', 'worksheets', 'materials', 'grades'), slug=slug
    )
    other_authors = Author.objects.exclude(pk=author.pk).only('slug', 'name')
    return render(request, 'literature/author_detail.html', {'author': author, 'other_authors': other_authors})


def material_stream(request, pk):
    material = get_object_or_404(Material.objects.exclude(file=''), pk=pk)
    return ranged_file_response(request, material.file, material.content_type)


@login_required
def material_download(request, pk):
    material = get_object_or_404(Material.objects.exclude(file=''), pk=pk)
    return FileResponse(
        open_or_404(material.file),
        as_attachment=True,
        filename=material.download_name,
        content_type=material.content_type,
    )
