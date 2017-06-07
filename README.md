# IsYourStartupDying?

### Classifier to answer the question:
Is it dying or nah?

Uses ML neighbor classifier algorithm to let budding entrepreneurs if their startup is successful or not, just enter your company details in, sit back, cross your fingers and read your result which was calculated based on pre-existing database of over 400,000 startups.

<p align="center">
<img src="http://33.media.tumblr.com/b5a4e7d76d422c02bd4065ef63fc5e3a/tumblr_inline_nqv4l5LKid1tn8yin_500.gif">
</p>

##### Current accuracy

~85% using k=20.

#### Usage
###### To test:

```$ python classify-startup.py -test {k_value}```

###### To classify your company:

```$ python classify-startup.py -n name -s status -m market -co country -ci city -ft funding value -fr funding rounds -ff first round date -lf last round date -r number of relationships -fo founded on -k {k_value}```

_Note:_ Multi word inputs must be surrounded by `''`

* name: Company name (it doesnt relly matter what this is)
* Status: `operating`, `aquired`, `ipo` or `closed`
* market: i.e `Tourism`, `'Real Estate'`, `'Music Services'`
* country: i.e `USA`, `Canada`, `'United Kingdom'`
* city: i.e `'San Franciso'`, `London`
* funding value: Total value to date i.e `2000000`
* funding rounds: i.e `3`
* first/last round date: Date of first and last funding, `YYYY-MM-DD`

ex: `$ python classify_startup.py -n Generic -s operating -m 'Real Estate' -co USA -ci 'San Francisco' -ft 2000000 -fr 1 -ff 2016-01-01 -lf 2016-01-01`
