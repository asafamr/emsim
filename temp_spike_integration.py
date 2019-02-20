from html.parser import HTMLParser
from typing import List, Tuple


class Sample:
    def __init__(self,
                 text: str,
                 subj_char_offsets: Tuple[int, int],
                 obj_char_offsets: Tuple[int, int],
                 trigger_char_offsets: Tuple[int, int],
                 relation="${label}",
                 subj_entity_type="${subject}",
                 obj_entity_type="${object}"):
        self.text = text
        self.subj_char_offsets = subj_char_offsets
        self.obj_char_offsets = obj_char_offsets
        self.trigger_char_offsets = trigger_char_offsets
        self.relation = relation
        self.subj_entity_type = subj_entity_type
        self.obj_entity_type = obj_entity_type


class SampleParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.relation = "${label}"
        self.sent = ""
        self.subj_char_start = None
        self.subj_char_end = None
        self.obj_char_start = None
        self.obj_char_end = None
        self.trigger_char_start = None
        self.trigger_char_end = None
        self.subj_ent = "${subject}"
        self.obj_ent = "${object}"
        self.samples = []

    def get_sample(self):
        if not self.sent:
            raise ValueError("A pattern was not specified")
        if self.subj_char_start is None:
            raise ValueError("An opening subject tag was not specified.")
        if self.subj_char_end is None:
            raise ValueError("A closing subject tag was not specified.")
        if self.obj_char_start is None:
            raise ValueError("An opening object tag was not specified.")
        if self.obj_char_end is None:
            raise ValueError("A closing object tag was not specified.")
        return Sample(self.sent,
                      (self.subj_char_start, self.subj_char_end),
                      (self.obj_char_start, self.obj_char_end),
                      (self.trigger_char_start, self.trigger_char_end) if self.trigger_char_start else None,
                      self.relation, self.subj_ent, self.obj_ent)

    def handle_starttag(self, tag, attrs):
        attrs = {i[0]: i[1] for i in attrs}
        if tag == "sample":
            if "relation" in attrs:
                self.relation = attrs["relation"]

        if tag == "s":
            self.subj_char_start = len(self.sent)
            if "type" in attrs:
                self.subj_ent = attrs["type"]

        elif tag == "o":
            self.obj_char_start = len(self.sent)
            if "type" in attrs:
                self.obj_ent = attrs["type"]

        elif tag == "t":
            self.trigger_char_start = len(self.sent)

    def handle_endtag(self, tag):
        if tag == "sample":
            self.samples.append(self.get_sample())
            self.sent = ''

        if tag == "s":
            self.subj_char_end = len(self.sent)

        elif tag == "o":
            self.obj_char_end = len(self.sent)

        elif tag == "t":
            self.trigger_char_end = len(self.sent)

    def handle_data(self, data):
        self.sent += data


class Bootstrapping(object):

    def get_candidate_sentences(self, seed_samples: List[Sample], max_docs: int) -> List[str]:
        """ Returns a list of sentences which ideally demonstrate different ways of expressing the relation specified
            by the seed samples
         Args:
            seed_samples (List[Sample]): a list of sample sentences, annotated with <s></s>, <o></o> and <t></t> tags.
            max_docs (int): the number of docs to fetch.
        :return:
        """
        raise NotImplementedError()

    def get_candidate_samples(self, seed_samples: List[Sample], max_docs: int) -> List[Sample]:
        """ Same as get_candidate_sentences, but returns samples annotated with subject and object."""

        raise NotImplementedError()


import json
import os
import requests
from dotenv import load_dotenv
load_dotenv()


class myBootstrapping(Bootstrapping):
    def get_candidate_sentences(self, seed_samples: List[Sample], max_docs: int) -> List[str]:
        """ Returns a list of sentences which ideally demonstrate different ways of expressing the relation specified
            by the seed samples
         Args:
            seed_samples (List[Sample]): a list of sample sentences, annotated with <s></s>, <o></o> and <t></t> tags.
            max_docs (int): the number of docs to fetch.
        :return:
        """

        positives = [x.text for x in seed_samples if not x.text.startswith('NEG:')]
        negatives = [x.text[4:].strip() for x in seed_samples if x.text.startswith('NEG:')]
        data = {'positives': positives, 'negatives': negatives,
                # these are optional:
                'dropout': 0.5,  # diversity: dropout #ntrails times with prob dropout
                'n_trials': 3,
                'neg_dist': 0.2,  # cosine dist from negatives to ignore
                'seed': 123,
                'n_per_page': max_docs,
                'page_num': 0
                }

        r = requests.post('http://%s:%s/getsim' % (os.environ['HOST'], os.environ['PORT']),
                          headers={'Content-Type': 'application/json'}, data=json.dumps(data))
        return r.json()['data']


if __name__ == '__main__':
    bootstrapper = myBootstrapping()
    seed_samples_strs = ["<sample><o>Paul Allen</o> <t>founder</t> of <s>Microsoft</s></sample>",
                         "<sample>NEG: I started the car engine </sample>"
                         ]
    sample_parser = SampleParser()
    sample_parser.feed("".join(seed_samples_strs))
    seed_samples = sample_parser.samples
    for x in bootstrapper.get_candidate_sentences(seed_samples, 10):
        print(x)
