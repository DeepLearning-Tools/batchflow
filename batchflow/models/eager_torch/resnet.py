"""
Kaiming He et al. "`Deep Residual Learning for Image Recognition
<https://arxiv.org/abs/1512.03385>`_"

Kaiming He et al. "`Identity Mappings in Deep Residual Networks
<https://arxiv.org/abs/1603.05027>`_"

Sergey Zagoruyko, Nikos Komodakis. "`Wide Residual Networks
<https://arxiv.org/abs/1605.07146>`_"

Xie S. et al. "`Aggregated Residual Transformations for Deep Neural Networks
<https://arxiv.org/abs/1611.05431>`_"
"""
import numpy as np
import torch.nn as nn

from .layers import ConvBlock
from .encoder_decoder import Encoder
from .utils import get_num_channels


CONV_LETTERS = ['c', 'C', 'w', 'W', 't', 'T']

class ResBlock(nn.Module):
    """ ResNet Module.  """
    def __init__(self, inputs=None, layout='cnacna', filters='same', kernel_size=3,
                 strides=1, downsample=False, bottleneck=False, groups=1, op='+', n_reps=1, **kwargs):
        #pylint: disable=eval-used
        super().__init__()

        num_convs = sum([letter in CONV_LETTERS for letter in layout])

        if isinstance(filters, str):
            filters = eval(filters, {}, {key: get_num_channels(inputs) for key in ['S', 'same']})

        filters = [filters] * num_convs if isinstance(filters, int) else filters
        kernel_size = [kernel_size] * num_convs if isinstance(kernel_size, int) else kernel_size
        strides = [strides] * num_convs if isinstance(strides, int) else strides
        strides_d = list(strides)
        groups = [groups] * num_convs
        side_branch_stride = np.prod(strides)
        side_branch_stride_d = int(side_branch_stride)

        if downsample:
            downsample = 2 if downsample is True else downsample
            strides_d[0] *= downsample
            side_branch_stride_d *= downsample
        if bottleneck:
            layout = 'cna' + layout + 'cna'
            kernel_size = [1] + kernel_size + [1]
            strides = [1] + strides + [1]
            strides_d = [1] + strides_d + [1]
            groups = [1] + groups + [1]
            bottleneck = 4 if bottleneck is True else bottleneck
            filters = [filters[0]] + filters + [filters[0] * bottleneck]
        layout = 'B' + layout + op

        layer_params = [{'strides': strides_d, 'side_branch/strides': side_branch_stride_d}] + [{}]*(n_reps-1)
        self.block = ConvBlock(*layer_params, inputs=inputs, layout=layout, filters=filters,
                               kernel_size=kernel_size, strides=strides, groups=groups,
                               side_branch={'layout': 'c', 'filters': filters[-1], 'strides': side_branch_stride},
                               **kwargs)

    def forward(self, x):
        return self.block(x)


class ResNet(Encoder):
    """ Base ResNet model.

    Parameters
    ----------


    """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['common/conv/bias'] = False
        config['initial_block'] += dict(layout='cnap', filters=64, kernel_size=7, strides=2,
                                        pool_size=3, pool_strides=2)

        config['body/encoder/num_stages'] = 4
        config['body/encoder/order'] = ['block']
        config['body/encoder/blocks'] += dict(base=ResBlock, layout='cnacna',
                                              filters=[64, 128, 256, 512],
                                              n_reps=[1, 1, 1, 1],
                                              downsample=[False, True, True, True],
                                              bottleneck=False)

        config['head'] += dict(layout='Vdf', dropout_rate=.4)

        config['loss'] = 'ce'

        return config

    def build_config(self):
        config = super().build_config()

        if config.get('head/units') is None:
            config['head/units'] = self.classes
        if config.get('head/filters') is None:
            config['head/filters'] = self.classes
        return config


class ResNet18(ResNet):
    """ The original ResNet-18 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/n_reps'] = [2, 2, 2, 2]
        return config


class ResNet34(ResNet):
    """ The original ResNet-34 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/n_reps'] = [3, 4, 6, 3]
        return config


class ResNet50(ResNet34):
    """ The original ResNet-50 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/layout'] = 'cna'
        config['body/encoder/blocks/bottleneck'] = True
        return config


class ResNet101(ResNet50):
    """ The original ResNet-101 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/n_reps'] = [3, 4, 23, 3]
        return config


class ResNet152(ResNet50):
    """ The original ResNet-152 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/n_reps'] = [3, 8, 36, 3]
        return config

class ResNeXt18(ResNet18):
    """ The ResNeXt-18 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/groups'] = 32
        return config


class ResNeXt34(ResNet34):
    """ The ResNeXt-34 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/groups'] = 32
        return config


class ResNeXt50(ResNet50):
    """ The ResNeXt-50 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/groups'] = 32
        return config


class ResNeXt101(ResNet101):
    """ The ResNeXt-101 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/groups'] = 32
        return config


class ResNeXt152(ResNet152):
    """ The ResNeXt-152 architecture. """
    @classmethod
    def default_config(cls):
        config = super().default_config()
        config['body/encoder/blocks/groups'] = 32
        return config
