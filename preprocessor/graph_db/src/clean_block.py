



class CleanBlock:
    def __init__(self, block, specification):
        self.block              = block
        self.specification      = specification
        self.cleaned_extrinsics = []
        self.cleaned_events     = []

    def clean(self):
        for extrinsic in self.block['extrinsics']:
            self.clean_extrinsic(extrinsic)

        for event in self.block['events']:
            self.clean_event(event)

        self.reassemble_block()
        return self.block

    def clean_extrinsic(self, extrinsic):
        call_module = extrinsic['call']['call_module']
        if call_module == "Balances":
            self.balances(extrinsic)
        elif call_module == "Staking":
            self.staking(extrinsic)
        elif call_module == "Utility":
            self.utility(extrinsic)
        elif call_module == "Proxy":
            self.proxy(extrinsic)
        else:
            self.cleaned_extrinsics.append(extrinsic)

    def clean_event(self, event):

        return

    def reassemble_block(self):
        self.block['extrinsics']    = self.cleaned_extrinsics
        self.block['events']        = self.cleaned_events

    def balances(self, extrinsic):
        clean_extrinsic = extrinsic
        call_function = extrinsic['call']['call_function']
        """        if self.specification in [0, 1, 5, ]:
            clean_extrinsic['clean_call'] = {}
            if call_function in ["transfer", "transfer_keep_alive","transfer_all"]:
                clean_extrinsic['clean_call']['to_address']  = extrinsic['call']['call_args'][0]['value']
                clean_extrinsic['clean_call']['amount']      = extrinsic['call']['call_args'][1]['value']
            if call_function in ["force_transfer"]:
                clean_extrinsic"""
        self.cleaned_extrinsics.append(clean_extrinsic)



        return clean_extrinsic


    def staking(self, extrinsic):
        return



