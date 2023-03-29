How to configure Service Catalog.

## Enforcing custom schema

Currently the contents of the `meta` field is unrestricted. However in an organisation maintaining or enforcing contents of `meta` might be desirable. To allow an organisation to enforce a particular format for the `meta` field, you can define your own schema.

1. Create a copy of `catalog/schemas/service.json` at a different location.
2. Link that location by setting a new value for `SERVICE_SCHEMA` to point to that location.
3. Customize the schema to meet your needs.

Example of changing just the `meta` section to enforce everyone to provide a `slack_channel` field:

```JSON
    "meta": {
        "type": "object",
        "patternProperties": {
            ".*": {
                "type": "string"
            }
        },
        "additionalProperties": false,
        "required": ["slack_channel"]
    }
```

For more information on JSON Schema, [check out this documentation](https://json-schema.org/).