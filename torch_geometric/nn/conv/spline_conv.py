import torch
from torch.nn import Parameter
from torch_spline_conv import SplineConv as Conv

from ..inits import uniform
from ..repeat import repeat


class SplineConv(torch.nn.Module):
    r"""The spline-based convolutional operator from the `"SplineCNN: Fast
    Geometric Deep Learning with Continuous B-Spline Kernels"
    <https://arxiv.org/abs/1711.08920>`_ paper

    .. math::
        \mathbf{x}^{\prime}_i = \frac{1}{|\mathcal{N}(i)|} \sum_{j \in
        \mathcal{N}(i)} \mathbf{x}_j \cdot
        h_{\mathbf{\Theta}}(\mathbf{e}_{i,j}),

    where :math:`h_{\mathbf{\Theta}}` denotes a kernel function defined
    over the weighted B-Spline tensor product basis.

    Args:
        in_channels (int): Size of each input sample.
        out_channels (int): Size of each output sample.
        dim (int): Pseudo-coordinate dimensionality.
        kernel_size (int or [int]): Size of the convolving kernel.
        is_open_spline (bool or [bool], optional): If set to :obj:`False`, the
            operator will use a closed B-spline basis in this dimension.
            (default :obj:`True`)
        degree (int, optional): B-spline basis degrees. (default: :obj:`1`)
        root_weight (bool, optional): If set to :obj:`False`, the layer will
            not add the transformed root node features to the output.
            (default: :obj:`True`)
        bias (bool, optional): If set to :obj:`False`, the layer will not learn
            an additive bias. (default: :obj:`True`)
    """

    def __init__(self,
                 in_channels,
                 out_channels,
                 dim,
                 kernel_size,
                 is_open_spline=True,
                 degree=1,
                 norm=True,
                 root_weight=True,
                 bias=True):
        super(SplineConv, self).__init__()

        self.in_channels = in_channels
        self.out_channels = out_channels
        self.degree = degree

        kernel_size = torch.tensor(repeat(kernel_size, dim), dtype=torch.long)
        self.register_buffer('kernel_size', kernel_size)

        is_open_spline = repeat(is_open_spline, dim)
        is_open_spline = torch.tensor(is_open_spline, dtype=torch.uint8)
        self.register_buffer('is_open_spline', is_open_spline)

        K = kernel_size.prod().item()
        self.weight = Parameter(torch.Tensor(K, in_channels, out_channels))

        if root_weight:
            self.root = Parameter(torch.Tensor(in_channels, out_channels))
        else:
            self.register_parameter('root', None)

        if bias:
            self.bias = Parameter(torch.Tensor(out_channels))
        else:
            self.register_parameter('bias', None)

        self.reset_parameters()

    def reset_parameters(self):
        size = self.in_channels * self.weight.size(0)
        uniform(size, self.weight)
        uniform(size, self.root)
        uniform(size, self.bias)

    def forward(self, x, edge_index, pseudo):
        """"""
        return Conv.apply(x, edge_index, pseudo, self.weight,
                          self._buffers['kernel_size'],
                          self._buffers['is_open_spline'], self.degree, True,
                          self.root, self.bias)

    def __repr__(self):
        return '{}({}, {})'.format(self.__class__.__name__, self.in_channels,
                                   self.out_channels)
