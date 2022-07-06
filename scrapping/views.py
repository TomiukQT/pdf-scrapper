from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from scrapping import scrapper

import scrapping.scrapper
from .models import Resolution, Voting, ExtendedResolution


def index(request):
    Resolution.objects.all().delete()
    ExtendedResolution.objects.all().delete()
    scrapper.refresh_data()

    res_list = Resolution.objects.all
    ex_res_list = ExtendedResolution.objects.all
    context = {
        'res_list': res_list,
        'ex_res_list': ex_res_list,
    }
    return render(request, 'index.html', context)


def detail(request, res_id):
    resolution = get_object_or_404(Resolution, pk=res_id)
    return render(request, 'detail.html', {'resolution': resolution})
