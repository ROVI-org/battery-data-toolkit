"""Write schemas to an RST-compatible table format"""
from batdata.schemas.cycling import RawData, CycleLevelData

print('Exporting schemas to RST...')

with open('column-schema.rst', 'w') as fp:
    for data_type in [RawData, CycleLevelData]:
        class_name = data_type.__name__
        print(f'``{class_name}``\n++{"+" * len(class_name)}++', file=fp)
        print(f'\n{data_type.__doc__}\n', file=fp)

        print('.. list-table::', file=fp)
        print('   :header-rows: 1\n', file=fp)
        print('   * - Column', file=fp)
        print('     - Description', file=fp)
        for name, field in data_type.model_fields.items():
            print(f'   * - {name}', file=fp)
            print(f'     - {field.description}', file=fp)
        print(file=fp)
