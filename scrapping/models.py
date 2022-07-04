import datetime

from django.db import models
from math import ceil


class Resolution(models.Model):
    name = models.CharField(max_length=50)
    text = models.CharField(max_length=1000)
    result_text = models.CharField(max_length=200)
    vote_yes = models.IntegerField(default=0)
    vote_no = models.IntegerField(default=0)
    vote_neutral = models.IntegerField(default=0)
    date = models.DateField(default=datetime.date(2020, 1, 1))
    category = models.CharField(max_length=50, default='Category')
    link = models.CharField(max_length=200, default='google.com')


    def voting_result(self):
        quorum = ceil((self.vote_yes + self.vote_no + self.vote_neutral)/2)
        return self.vote_yes >= quorum

    def get_header(self):
        return self.name if len(self.name) <= 60 else f'{self.name[0:60]}...'

    def __str__(self):
        return self.name


class ExtendedResolution(Resolution):
    result = models.BooleanField()


class Representative(models.Model):
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    party = models.CharField(max_length=40)
    #titles_front = models.CharField(max_length=20)
    #titles_back = models.CharField(max_length=20)


class Voting(models.Model):
    option = models.CharField(max_length=20)
    voted_by = models.ForeignKey(Representative, on_delete=models.CASCADE)
    voted_on = models.ForeignKey(ExtendedResolution, on_delete=models.CASCADE)


