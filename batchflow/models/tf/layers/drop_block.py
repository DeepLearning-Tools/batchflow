"""
Golnaz Ghiasi, Tsung-Yi Lin, Quoc V. Le "`DropBlock: A regularization method for convolutional networks
<https://arxiv.org/pdf/1810.12890.pdf>`_"
"""

import tensorflow as tf
from .pooling import max_pooling

# TODO:
# Add scheduler to gradually increase dropout_rate from 0 to target value.
# When max_pooling allows for dynamic kernel size, implement block_size as fraction
# of spatial_dims.

def dropblock(inputs, dropout_rate, block_size, is_training, data_format, seed=None):
    """ Drop Block module.

    Parameters
    ----------
    inputs : tf.Tensor
        Input tensor
    dropout_rate : float
        Default is 0
    block_size : int or float or tuple of ints or floats
        Size of the block to drop. If tuple, should be of the same size as spatial
        dimensions of inputs.
        If float < 0, block_size is calculated as a fraction of corresponding spatial
        dimension.
    is_training : bool or tf.Tensor
        Default is True.
    seed : int
        seed to use in tf.distributions.Bernoulli.sample method.
    data_format : str
        `channels_last` or `channels_first`. Default - 'channels_last'.

    Returns
    -------
    tf.Tensor
    """
    return tf.cond(tf.logical_or(tf.logical_not(is_training), tf.equal(dropout_rate, 0.0)),
                   true_fn=lambda: inputs,
                   false_fn=lambda: _dropblock(inputs, dropout_rate, block_size, seed, data_format),
                   name='dropblock')

def _dropblock(inputs, dropout_rate, block_size, seed, data_format):
    """
    """
    one = tf.convert_to_tensor([1], dtype=tf.int32)
    zeros_pad = tf.convert_to_tensor([[0, 0]], dtype=tf.int32)

    input_shape = tf.shape(inputs)

    if data_format == 'channels_first':
        spatial_dims, channels = input_shape[2:], input_shape[1:2]
    else:
        spatial_dims, channels = input_shape[1:-1], input_shape[-1:]
    spatial_ndim = spatial_dims.get_shape().as_list()[0]

    if isinstance(block_size, int):
        block_size = [block_size] * spatial_ndim
        block_size_tf = tf.convert_to_tensor(block_size)
    elif isinstance(block_size, tuple):
        if len(block_size) != spatial_ndim:
            raise ValueError('Length of `block_size` should be the same as spatial dimensions of input.')
        block_size_tf = tf.convert_to_tensor(block_size, dtype=tf.int32)
    else:
        raise ValueError('block_size should be int or tuple!')
    block_size_tf = tf.math.minimum(block_size_tf, spatial_dims)
    block_size_tf = tf.math.maximum(block_size_tf, one)

    spatial_dims_float = tf.cast(spatial_dims, dtype=tf.float32)
    block_size_tf_float = tf.cast(block_size_tf, dtype=tf.float32)

    inner_area = spatial_dims - block_size_tf + one
    inner_area_float = tf.cast(inner_area, dtype=tf.float32)

    gamma = (tf.convert_to_tensor(dropout_rate) * tf.math.reduce_prod(spatial_dims_float) /
             tf.math.reduce_prod(block_size_tf_float) / tf.math.reduce_prod(inner_area_float))

    # Mask is sampled for each featuremap independently and applied identically to all batch items
    noise_dist = tf.distributions.Bernoulli(probs=gamma, dtype=tf.float32)

    if data_format == 'channels_first':
        sampling_mask_shape = tf.concat((one, channels, inner_area), axis=0)
    else:
        sampling_mask_shape = tf.concat((one, inner_area, channels), axis=0)
    mask = noise_dist.sample(sampling_mask_shape, seed=seed)

    left_spatial_pad = (block_size_tf - one) // 2
    right_spatial_pad = block_size_tf - one - left_spatial_pad
    spatial_pads = tf.stack((left_spatial_pad, right_spatial_pad), axis=1)
    if data_format == 'channels_first':
        pad_shape = tf.concat((zeros_pad, zeros_pad, spatial_pads), axis=0)
    else:
        pad_shape = tf.concat((zeros_pad, spatial_pads, zeros_pad), axis=0)
    mask = tf.pad(mask, pad_shape)

    # Using max pool operation to extend sampled points to blocks of desired size
    pool_size = block_size
    strides = [1] * spatial_ndim
    mask = max_pooling(mask, pool_size=pool_size, strides=strides,
                       data_format=data_format, padding='same')
    mask = tf.cast(1 - mask, tf.float32)
    output = tf.multiply(inputs, mask)

    # Scaling the output as in inverted dropout
    output = output * tf.to_float(tf.size(mask)) / tf.reduce_sum(mask)
    return output
