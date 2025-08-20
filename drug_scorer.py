# -*- coding: utf-8 -*-
import re, numpy as np
WEIGHTS=np.array([0.7841198794598256, 0.6936287055262979, 0.6598222472386498, 0.9096115916498606, 0.7492912860059341, 0.6238784170381078, 0.629817713403088, 0.5068378702719317, -0.787489734716512],dtype=float)
THRESHOLD=0.44000000000000006
MALAY=set(['g4nj4', 'drop', 'pukal', 'urusan senyap', 'pil tidur', 'malam', 'sy4bu', 'pil kuda', 'ready stock', 'mlm', 'barang jalan', 'selit', 'ubat kuat', 'packing', 'bankin', 'barang sampai', 'barang', 'duit', 'transfer', 'stok', 'pagi', 'runner', 'bayar', 'ganja', 'cod', 'syabu', 'ketum', 'titip'])
CHINESE=set(['粉', '安全', '大麻', '现货', '现金', '私聊', '便宜点', '毒', '老地方', '草', '见面', '冰毒', '白粉', '冰', '试下', 'K粉', '货', '药丸', '朋友介绍'])
ENGLISH=set(['bulk', 'private', 'drop', 'ice', 'pills', 'tabs', 'm3th', 'secure', 'meet', 'weed', 'powder', 'cash', 'xtc', 'k2', 'delivery', 'stuff', 'stealth', 'w33d', 'quiet', 'coke', 'meth', 'stock', 'ganja', 'p1lls', 'mdma', 'discount', 'ecstasy'])
EMOJI=set(['💊', '🍁', '💉', '🧪', '💵', '📦', '🔒', '🤫', '🪙'])
MONEY=set(['rm', 'ringgit', 'cash', 'duit', 'bayar', 'transfer', 'bankin', 'tng', 'sikit', 'seratus', '50', '100', '200'])
SECRECY=set(['senyap', 'diam', 'private', 'confidential', 'silent', '🤫', '🔒', '安全', '私聊', 'low key', 'dl'])
QTY=set(['1g', '2g', '3g', '5g', '10g', 'setengah', 'sekilo', 'kg', 'pkt', 'pack', 'botol', 'strip', '板', '粒'])
def _featurize(msg:str)->np.ndarray:
    text=(msg or "").lower()
    emoji_cnt=sum(text.count(e) for e in EMOJI)
    tokens=re.findall(r"[\u4e00-\u9fff]|[a-zA-Z0-9]+", text)
    def count_in(tok,v): return sum(1 for t in tok if t in v)
    mal=count_in(tokens,MALAY)
    chn=count_in(tokens,CHINESE)+sum(1 for t in tokens if re.match(r"[\u4e00-\u9fff]",t) and t in "".join(list(CHINESE)))
    eng=count_in(tokens,ENGLISH)
    money_c=count_in(tokens,MONEY)
    sec_c=count_in(tokens,SECRECY)
    qty_c=count_in(tokens,QTY)
    nums=len(re.findall(r"\b\d+g?\b", text))
    return np.array([mal,chn,eng,emoji_cnt,money_c,sec_c,qty_c,nums,1.0],dtype=float)
def score_message(msg:str)->float:
    x=_featurize(msg); z=float(x@WEIGHTS); return 1/(1+np.exp(-z))
def is_drug(msg:str)->bool: return score_message(msg)>=THRESHOLD
def batch_score(messages): return [score_message(m) for m in messages]
