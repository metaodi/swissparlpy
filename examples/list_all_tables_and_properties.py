import swissparlpy

# print all tables with their properties

overview = swissparlpy.get_overview()
for table, props in overview.items():
    print(table)
    for prop in props:
        print(f' + {prop}')
    print('')
