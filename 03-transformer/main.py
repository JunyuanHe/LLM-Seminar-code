import torch
import torch.nn as nn

PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

device = torch.device("cuda" if torch.cuda.is_available() else "mps" if getattr(torch, "has_mps", False) and torch.backends.mps.is_available() else "cpu")
