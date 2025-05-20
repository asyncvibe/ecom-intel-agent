# from bson import ObjectId
# from pydantic_core import CoreSchema, core_schema
# from typing import Any

# class PyObjectId(ObjectId):
#     @classmethod
#     def __get_pydantic_core_schema__(
#         cls,
#         _source_type: Any,
#         _handler: Any,
#     ) -> CoreSchema:
#         return core_schema.json_or_python_schema(
#             json_schema=core_schema.str_schema(),
#             python_schema=core_schema.union_schema([
#                 core_schema.is_instance_schema(ObjectId),
#                 core_schema.no_info_plain_validator_function(lambda x: ObjectId(x) if ObjectId.is_valid(x) else x)
#             ])
#         )
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: type, handler: GetCoreSchemaHandler) -> CoreSchema:
        def validate(value: str) -> ObjectId:
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid ObjectId")
            return ObjectId(value)
        return core_schema.union_schema(
            [
                core_schema.str_schema(),
                core_schema.is_instance_schema(ObjectId)
            ],
            serialization=core_schema.to_string_ser_schema()
        )
