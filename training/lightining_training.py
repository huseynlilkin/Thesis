import os
import wandb

from pytorch_lightning import seed_everything
from pytorch_lightning.loggers import WandbLogger

import config
from training.datasets import DFDCLightningDataset
from training.model_zoo import EfficientNet, DeiT
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint

os.environ['REQUESTS_CA_BUNDLE'] = 'C:/Users/Ilkin/Downloads/piktiv-cacert.pem'


def train_fn():
    wandb_logger = WandbLogger(project='sweep-test')
    cfg = wandb_logger.experiment.config

    model = EfficientNet(cfg, version='b0')
    # model = DeiT()
    checkpoint_callback = ModelCheckpoint(
        monitor='val_loss',
        dirpath=f'{config.CHECKPOINT_PATH}',
        filename='sample-xxx-{epoch:02d}-{val_loss:.4f}',
        save_last=True,
        mode='min',
    )
    dataset = DFDCLightningDataset(cfg)
    trainer = pl.Trainer(gpus=cfg.gpus, precision=cfg.precision,
                         logger=wandb_logger,
                         accumulate_grad_batches=cfg.accumulate_grad_batches,
                         reload_dataloaders_every_epoch=True,
                         check_val_every_n_epoch=1,
                         log_every_n_steps=10,
                         resume_from_checkpoint=os.path.join(config.CHECKPOINT_PATH,
                                                             'sample-xxx-epoch=19-val_loss=0.6676.ckpt'),
                         callbacks=[checkpoint_callback],
                         max_epochs=cfg.epochs,
                         default_root_dir=config.CHECKPOINT_PATH,
                         limit_train_batches=10,
                         limit_val_batches=10
                         )
    trainer.fit(model, dataset)


def tune_hyper_params():
    sweep_config = {
        "method": "random",  # Random search
        "metric": {  # We want to maximize val_acc
            "name": "val_loss",
            "goal": "minimize"
        },
        "parameters": {
            "batch_size": {
                # Choose from pre-defined values
                "values": [32, 64]
            },
            "precision": {
                # Choose from pre-defined values
                "values": [16, 32]
            },
            "lr": {
                # log uniform distribution between exp(min) and exp(max)
                "distribution": "log_uniform",
                "min": -9.21,  # exp(-9.21) = 1e-4
                "max": -4.61  # exp(-4.61) = 1e-2
            }
        }
    }

    sweep_id = wandb.sweep(sweep_config, project='sweep-test')
    wandb.agent(sweep_id, function=train_fn)


if __name__ == '__main__':
    seed_everything(99)

    wandb.login(key='c4e2ebb0c3dbe0876676fb7d125f81c39bbc7367')
    tune_hyper_params()
