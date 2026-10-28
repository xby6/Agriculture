"""Pure-PyTorch inference model equivalent to the trained PyG model.

The training graph is a fully connected 8-node graph without self edges.
PyG's GCNConv adds the missing self edges, so its normalized adjacency is an
8x8 matrix filled with 1/8.  This lets inference avoid torch_geometric while
preserving the trained computation.
"""

import math

import torch
from torch import nn
from torch.nn import functional as F


class CompleteGraphConv(nn.Module):
    """GCNConv specialized for a batch of fixed-size complete graphs."""

    def __init__(self, in_dim: int, out_dim: int) -> None:
        super().__init__()
        self.bias = nn.Parameter(torch.empty(out_dim))
        self.lin = nn.Linear(in_dim, out_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Equivalent to normalized aggregation after PyG adds self-loops.
        graph_mean = x.mean(dim=1, keepdim=True)
        return self.lin(graph_mean).expand(-1, x.size(1), -1) + self.bias


class DotProductAttention(nn.Module):
    def __init__(self, hidden_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        del hidden_dim
        self.drop = nn.Dropout(dropout)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        d = h.size(-1)
        scores = torch.matmul(h, h.transpose(1, 2)) / math.sqrt(float(d))
        z = torch.matmul(torch.softmax(scores, dim=-1), h)
        return self.drop(z)


class LiquidGateAttention(nn.Module):
    def __init__(
        self,
        hidden_dim: int,
        steps: int = 1,
        delta: float = 1.0,
        eps: float = 1e-4,
        tau_min: float = 1.6,
    ) -> None:
        super().__init__()
        self.steps = steps
        self.delta = delta
        self.eps = eps
        self.tau_min = tau_min
        # Retained because the training checkpoint contains these parameters.
        self.out_fc = nn.Linear(hidden_dim, hidden_dim)
        self.tau_fc = nn.Linear(hidden_dim * 2, 1)
        self.ln = nn.LayerNorm(hidden_dim)
        self.drop = nn.Dropout(0.1)

    def forward(self, h: torch.Tensor) -> torch.Tensor:
        out = h
        for _ in range(self.steps):
            d = out.size(-1)
            scores = torch.matmul(out, out.transpose(1, 2)) / math.sqrt(float(d))
            z = torch.matmul(torch.softmax(scores, dim=-1), out)
            z = self.drop(z)
            tau = self.tau_min + F.softplus(
                self.tau_fc(torch.cat((out, z), dim=-1))
            ) + self.eps
            alpha = 1.0 - torch.exp(-self.delta / tau)
            out = self.ln(out + alpha * (z - out))
        return out


class ResGCNBlockWithDotAttention(nn.Module):
    def __init__(self, in_dim: int, out_dim: int, dropout: float = 0.1) -> None:
        super().__init__()
        self.conv = CompleteGraphConv(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)
        self.proj = nn.Linear(in_dim, out_dim) if in_dim != out_dim else None
        self.attention = DotProductAttention(out_dim, dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x if self.proj is None else self.proj(x)
        h = self.norm(self.conv(x))
        return F.relu(res + self.attention(h))


class ResGCNBlockWithGateAttention(nn.Module):
    def __init__(self, in_dim: int, out_dim: int) -> None:
        super().__init__()
        self.conv = CompleteGraphConv(in_dim, out_dim)
        self.norm = nn.LayerNorm(out_dim)
        self.proj = nn.Linear(in_dim, out_dim) if in_dim != out_dim else None
        self.attention = LiquidGateAttention(out_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = x if self.proj is None else self.proj(x)
        h = self.norm(self.conv(x))
        return F.relu(res + self.attention(h))


class ResidualLiquidGateGCN(nn.Module):
    """Four-class classifier accepting float tensors shaped [B, 8, 9]."""

    def __init__(
        self,
        in_dim: int = 9,
        hidden: int = 72,
        num_classes: int = 4,
        num_channels: int = 8,
        ch_emb_dim: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.num_channels = num_channels
        self.dropout = dropout
        self.ch_emb = nn.Embedding(num_channels, ch_emb_dim)
        self.in_proj = nn.Linear(in_dim + ch_emb_dim, hidden)
        self.block1 = ResGCNBlockWithDotAttention(hidden, hidden, 0.1)
        self.block2 = ResGCNBlockWithGateAttention(hidden, hidden)
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(hidden, num_classes))

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        if patches.dim() != 3:
            raise ValueError("patches must have shape [batch, 8, 9]")
        if patches.size(1) != self.num_channels or patches.size(2) != 9:
            raise ValueError("expected patches with shape [batch, 8, 9]")

        batch_size = patches.size(0)
        ch_id = torch.arange(self.num_channels, device=patches.device)
        ch_e = self.ch_emb(ch_id).unsqueeze(0).expand(batch_size, -1, -1)
        x = F.relu(self.in_proj(torch.cat((patches, ch_e), dim=-1)))
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.block1(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.block2(x)
        return self.head(x.mean(dim=1))


class HeatmapModel(nn.Module):
    """Deployment wrapper returning the predicted heat-map class 0..3."""

    def __init__(self, classifier: ResidualLiquidGateGCN) -> None:
        super().__init__()
        self.classifier = classifier

    def forward(self, patches: torch.Tensor) -> torch.Tensor:
        return torch.argmax(self.classifier(patches), dim=1)
