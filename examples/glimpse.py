import swissparlpy

glimpse = swissparlpy.get_glimpse("Canton", 10)
for r in glimpse:
    print(r)
