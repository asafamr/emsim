import pandas as pd
import numpy as np
import os
import json
import spacy
from sklearn.neighbors import KDTree
from sklearn.preprocessing import normalize
import os

SPACY_MODEL = 'en_core_web_lg'

corpus = None
kd_tree = None
nlp = None


def _cos_dist_to_normed_euc(cos_dist_query):
    cos_dist_query_rad = np.arccos(1 - cos_dist_query)
    euc_dist = np.sin(cos_dist_query_rad / 2) * 2
    return euc_dist


def _gen_samples(pos_vecs):
    n_ret = 20
    returned = set()
    while True:
        dists, queried = kd_tree.query(pos_vecs, n_ret)
        queried = np.concatenate(queried)
        dists = np.concatenate(dists)
        order = np.argsort(dists)
        for i in order:
            this_idx = queried[i]
            this_dist = dists[i]
            if this_idx in returned or this_dist < 0.01:
                continue
            returned.add(this_idx)
            yield this_idx
        n_ret *= 2


def preload():
    global corpus, kd_tree, nlp

    print('loading spacy model...')
    nlp = spacy.load(SPACY_MODEL)

    print('loading tacred ds...')
    ds_location = os.getenv("DS_LOCATION")
    rows = []
    for idx, f in enumerate(os.listdir(ds_location)):
        with open(os.path.join(ds_location, f)) as fin:
            js = json.load(fin)
            sent = js['sentences'][0]
            rows.append([f] + [sent[x] for x in 'entities words tags'.split()])
    df = pd.DataFrame(rows, columns='filename entities words tags'.split())
    df['text'] = df.words.map(lambda x: ' '.join(x))
    corpus = df.groupby(['text']).first().reset_index()['text'].values

    vecs = []
    for txt in corpus:
        vec = nlp(txt, disable=['ner', 'parser', 'tagger']).vector
        vecs.append(vec)
    vecs = normalize(np.array(vecs))

    print('building search tree...')
    kd_tree = KDTree(vecs)

    print('done.')


def get_close_sents(positives, negatives, dropout, n_trials, neg_dist, seed, n_per_page, page_num):
    np.random.seed(seed)
    p_vectors = normalize([nlp(x, disable=['ner', 'parser', 'tagger']).vector for x in positives])

    stop_list = set()
    if negatives:
        n_vectors = normalize([nlp(x, disable=['ner', 'parser', 'tagger']).vector for x in negatives])
        neg_dist_euc = _cos_dist_to_normed_euc(neg_dist)
        stop_list = set(kd_tree.query_radius(n_vectors, neg_dist_euc)[0])

    sampled_means = []

    for x in range(n_trials):
        mask = 0
        while np.sum(mask) == 0:
            mask = np.random.uniform(size=len(positives)) < dropout
        sampled_means.append(np.mean(p_vectors[mask], 0))

    sampled_means = normalize(sampled_means)

    current_page = 0
    ret = []
    for x in _gen_samples(sampled_means):
        if x in stop_list:
            continue
        ret.append(x)
        if len(ret) == n_per_page:
            if current_page == page_num:
                break
            else:
                ret = []
                current_page += 1

    return list(corpus[ret])
