from lightning.pytorch.callbacks import BaseFinetuning


class BackboneFreezeUnfreeze(BaseFinetuning):
    def __init__(self, unfreeze_at_epoch=10):
        super().__init__()
        self._unfreeze_at_epoch = unfreeze_at_epoch

    def freeze_before_training(self, pl_module):
        self.freeze(pl_module.backbone)
        params = list(pl_module.parameters())
        active = list(filter(lambda p: p.requires_grad, params))
        print(f"active: {len(active)}, all: {len(params)}")

    def finetune_function(self, pl_module, current_epoch, optimizer):
        if current_epoch == self._unfreeze_at_epoch:
            self.unfreeze_and_add_param_group(
                modules=pl_module.backbone,
                optimizer=optimizer,
                train_bn=True,
            )
        params = list(pl_module.parameters())
        active = list(filter(lambda p: p.requires_grad, params))
        print(f"active: {len(active)}, all: {len(params)}")
