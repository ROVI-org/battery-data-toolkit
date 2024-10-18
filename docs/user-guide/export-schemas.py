"""Write schemas to an RST-compatible table format"""
from typing import TextIO, get_args, Optional, get_origin

from pydantic import BaseModel

from batdata.schemas.cycling import RawData, CycleLevelData
from batdata.schemas import BatteryMetadata

print('Exporting column schemas to RST...')

with open('column-schema.rst', 'w') as fp:
    for data_type in [RawData, CycleLevelData]:
        class_name = data_type.__name__
        print(f'``{class_name}``\n++{"+" * len(class_name)}++', file=fp)
        print(f'\n**Source Object**: :class:`{data_type.__module__}.{data_type.__name__}`\n', file=fp)
        print(f'\n{data_type.__doc__}\n', file=fp)

        print('.. list-table::', file=fp)
        print('   :header-rows: 1\n', file=fp)
        print('   * - Column', file=fp)
        print('     - Description', file=fp)
        for name, field in data_type.model_fields.items():
            print(f'   * - {name}', file=fp)
            print(f'     - {field.description}', file=fp)
        print(file=fp)


# Export the metadata schemas recursively
print('Exporting metadata formats')
def expand_terms(metadata_cls: type[BaseModel], fo: TextIO):
    """Export the data in column format"""

    to_recurse = set()

    class_name = metadata_cls.__name__
    print(f'``{class_name}``\n~~{"~" * len(class_name)}~~', file=fo)
    print(f'\n**Source Object**: :class:`{metadata_cls.__module__}.{class_name}`\n', file=fo)
    print(f'\n{metadata_cls.__doc__}\n', file=fo)

    print('.. list-table::', file=fo)
    print('   :header-rows: 1\n', file=fo)
    print('   * - Column', file=fo)
    print('     - Type', file=fo)
    print('     - Description', file=fo)
    for name, field in metadata_cls.model_fields.items():
        print(f'   * - {name}', file=fo)

        # Expand the type annotation
        is_optional = field.is_required()
        if (subtypes := get_args(field.annotation)) != ():
            is_optional = True
            print(f'     - {", ".join(x.__name__ if isinstance(x, type(object)) else str(x) for x in subtypes if not x == type(None))}', file=fp)
        else:
            print(f'     - {field.annotation.__name__}', file=fo)

        # Prepare to recurse
        for cls_type in [field.annotation, *subtypes]:
            if isinstance(cls_type, BaseModel.__class__):
                to_recurse.add(cls_type)

        print(f'     - {"(**Required**) " if not is_optional else ""}{str(field.description)}', file=fo)
    print(file=fo)

    for cls_type in to_recurse:
        expand_terms(cls_type, fo)


with open('metadata-schema.rst', 'w', encoding='utf-8') as fp:
    expand_terms(BatteryMetadata, fp)
