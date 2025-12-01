import regex as re
from collections import Counter

PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""

text = "this is a cat, is a cat."
gen = [m.group() for m in re.finditer(PAT, text)]
print(gen)
table = Counter(gen)




t = ("a", "bde", "c")
lst = [1,3,5,7,9]
print(" ".join(map(str, lst)))