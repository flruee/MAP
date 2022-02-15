# Data handling

# Example transfer transaction

```
 {
            "extrinsic_hash": "0xd81674f8cad11cbfae6f244d1692080577e88afbef854d84622b216e487e8a2d", // id for transaction, it is not unique accross blocks.
            "extrinsic_length": 144, //seems unimportant
            "address": "12eWH5FAw4F9CsQDhkqG6xdo5AHjnqWLw4BzZ4mcYpq4ZUMh", // transaction starter
            "signature": {
                "Sr25519": "0x0e65bddaf983b956a1b2d50fe5fc23bc9a0e3aadb5f5ea6fc70eb9d33efcc923df2871e3b8a184db4a75ed596d56f6f1017e742e1bd65860dd83f6ae4035e68e"
            }, //signed transaction?
            "era": [
                64,
                40
            ], // what is this exactly
            "nonce": 9, 
            "tip": 0,
            "call": {
                "call_index": "0x0503", //what is this?
                "call_function": "transfer_keep_alive", // keep, but probably encode differently
                "call_module": "Balances",
                "call_args": [
                    {
                        "name": "dest",
                        "type": "LookupSource",
                        "value": "16VE4xFGoDj24d2brvKeW43bWzMHueoqQHNgFMaEki3FPsiv"
                    },
                    {
                        "name": "value",
                        "type": "Balance",
                        "value": 435000000000
                    }
                ],
                "call_hash": "0x6ba4c4f48ddef1b1560fa2be94482dc2973519eeef70b888c5720801ac4f7e23" //what is this
            }
        },
```
