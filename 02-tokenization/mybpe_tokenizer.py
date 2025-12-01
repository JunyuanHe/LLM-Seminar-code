import regex as re
from collections import Counter, defaultdict

PAT = r"""'(?:[sdmt]|ll|ve|re)| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+"""





# s_encoded = s.encode("utf-8")
# print(s[0])
# print(s_encoded[6])


def train_bpe_naive(text: str, num_merges: int) -> tuple[ dict[int, bytes], list[tuple[bytes, bytes]] ]:
    # 1. Initialize vocab, 0-225+special token
    vocab = {i: bytes([i]) for i in range(256)}
    vocab[256] = "<|endoftext|>".encode("utf-8")


    # 2. pre-tokenization: construct the frequency table
    freq_table = Counter(m.group() for m in re.finditer(PAT, text))
    freq_table_tuple = {tuple(bytes([x]) for x in key.encode("utf-8")) : value for key, value in freq_table.items() } 
    # print(freq_table)
    # print(freq_table_tuple)

    # freq_table_tuple = {}
    # for key, value in freq_table.item():
    #     freq_table_tuple[tuple(bytes([x]) for x in key.encode("utf-8"))] = value

    # 3. merge
    merges = []
    for i in range(num_merges):
        # get statistics for each adjacent pair
        pair_stats = defaultdict(int)
        for key, value in freq_table_tuple.items():
            for j in range(len(key)-1):
                pair_stats[(key[j], key[j+1])] += value
        
        # print(pair_stats)

        # get the most frequent pair
        # best_pair1 = max(pair_stats, key=pair_stats.get)
        best_pair = max(pair_stats, key=lambda k: (pair_stats[k], k))
        # print(best_pair1)
        # print(best_pair)

        # append merged byte to vocab
        print(b''.join(best_pair))
        vocab[257 + i] = b''.join(best_pair)

        # save the merges
        merges.append(best_pair)

        # merge in the frequency table
        freq_table_tuple = merge_pair_in_table(freq_table_tuple, best_pair)

    return vocab, merges


def merge_pair(tup: tuple[bytes], pair: tuple[bytes]) -> tuple[bytes]:
    result = []
    i = 0
    while i < len(tup):
        if tup[i:i+2] == pair:
            result.append(b''.join(pair))
            i += 2
        else:
            result.append(tup[i])
            i += 1
    return tuple(result)

def merge_pair_in_table(table: dict[tuple[bytes], int], pair: tuple[bytes]) -> dict[tuple[bytes], int]:
    return {merge_pair(key, pair): value for key, value in table.items()}





class Tokenizer:
    def __init__(self, vocab: dict[int, bytes], merges: list[tuple[bytes, bytes]]):
        self.id2token: dict[int, bytes] = vocab 
        self.token2id: dict[bytes, int] = {vocab[i]:i for i in vocab}   # {v: k for k, v in vocab.items()}
        # self.vocab = vocab
        self.merges = merges

    def encode(self, text: str) -> list[int]:
        '''
        Encode an input text into a sequence of token IDs.
        '''
        # 1. pre-tokenize
        pretokens = re.finditer(PAT, text)

        # 2. loop through pretokens
        encoded = []
        for m in pretokens:
            # Apply the merges: m: tuple[bytes] -> tuple[bytes] 
            # merges: [("a", "t"), ("c", "at")] 
            # vocab: {0-25: 26-letters, 26: "at", 27: "cat"}
            # e.g. ("c", "a", "t", "s") -> ("c", "at", "s") -> ("cat", "s")
            pretoken_tuple = tuple( bytes([x]) for x in m.group().encode("utf-8") )
            
            for pair in merges:
                pretoken_tuple = merge_pair(pretoken_tuple, pair)

            # Look up ids according to token2id
            # -> (27, 19)
            for token in pretoken_tuple:
                # Look up ids
                token_id = self.token2id.get(token)
                # token_id = self.token2id[token]
                if token_id is None:
                    raise ValueError(f"Unknown token: {token}")
                encoded.append(token_id)

        return encoded

    def decode(self, ids: list[int]) -> str:
        '''
        Decode a sequence of token IDs into text.
        '''
        token_seq = [self.id2token[id] for id in ids]
        byte_seq = b"".join(token_seq) # bytes
        return byte_seq.decode("utf-8", errors="replace")

        






if __name__ == '__main__':
    text = "low low low lower lower widest widest newest"
    vocab, merges = train_bpe_naive(text, 5)
    print(vocab)
    print(merges)

    tok = Tokenizer(vocab, merges)

    text2 = "fastest train stops"
    encoded = tok.encode(text2)
    print(encoded)
    decoded = tok.decode(encoded)
    print(decoded)

    # # Mary said 'go!'
    # s = "Mary said 'go!'"
    # # s = 'Mary said \'go!\''
    # print(s)

    