import spacy
from spacy.util import filter_spans
from spacy.matcher import PhraseMatcher
import nltk
from nltk.corpus import brown
import re
from rapidfuzz import fuzz
import duckdb as dd
import os
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "../Data/idiom_repository_all.parquet"))

class Idioms():
    def __init__(self):
        self.idiom_df = dd.query(f"""
            SELECT definition, CAST(variations AS VARCHAR[]) || [idiom] AS all_variations
            FROM read_parquet('{DATA_PATH}')
        """).df()

        self.nlp = spacy.load("en_core_web_sm")

        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.patterns = [self.nlp.make_doc(p) for q in self.idiom_df['all_variations'] for p in q]
        self.matcher.add("PHRASES", self.patterns)
        self.phrase_to_definition = {}

        for _, row in self.idiom_df.iterrows():
            for phrase in row["all_variations"]:
                # if we make a column that has generic replacements, we can use that instead of definitions
                self.phrase_to_definition[self.normalize(phrase)] = row["definition"]

    def pick_out_idioms(self, input: str) -> list[tuple[str, int, int]]:
        doc = self.nlp(input)
        matches = self.matcher(doc)
        return [(doc[start: end].text, start, end) for _, start, end in matches]

    def normalize(self, s: str) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s]", "", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def find_best_definition(self, user_input, threshold=80):
        q = self.normalize(user_input)
        best = None
        best_score = -1

        for idx, row in self.idiom_df.iterrows():
            for phrase in row["all_variations"]:
                score = fuzz.ratio(q, self.normalize(phrase))
                if score > best_score:
                    best_score = score
                    best = idx

        if best_score >= threshold:
            return self.idiom_df.loc[best]["definition"]
        return None

    def find_idiom_matches(self, text: str):
        doc = self.nlp(text)
        raw_matches = self.matcher(doc)
        spans = [doc[start:end] for _, start, end in raw_matches]
        spans = filter_spans(spans)

        results = []
        for span in spans:
            definition = self.phrase_to_definition.get(self.normalize(span.text))
            if definition:
                results.append({
                    "text": span.text,
                    "definition": definition,
                    "start": span.start_char,
                    "end": span.end_char,
                })
        return results
    
    def llm_fix_grammar(self, sentence, idiom_matches):
        for match in idiom_matches:
            idiom = match["text"]
            definition = match["definition"]

            prompt = f"""
            Original sentence: "{sentence}"
            Replace the phrase "{idiom}" with the definition "{definition}".
            Rewrite the sentence so that it is grammatically perfect and natural.
            Do not edit the non-idiom part unless it is for grammar.
            Only return the corrected sentence. No explanation.
            """

            res = requests.post("http://localhost:11434/api/generate",
                                    json={
                                        "model": "llama3",
                                        "prompt": prompt,
                                        "stream": False
                                    })
            if (res.status_code == 200):
                sentence = res.json()["response"].strip()
            
        return sentence

    def replace_idioms_with_definitions(self, text: str) -> str:
        matches = self.find_idiom_matches(text)

        res = self.llm_fix_grammar(text, matches)

        if (res != text):
            return res
        
        for match in reversed(matches):
            text = text[:match["start"]] + match["definition"] + text[match["end"]:]
        return text

    def respond(self, input: str) -> str:
        if re.fullmatch(r"^.*[Dd]o you love me[.?]?", input):
            return "No, I only love idioms and you'll never be them."
        elif re.fullmatch(r"^.*[Ww]hat does (?:the idiom )?([\"]?.*?[\"]?) mean[.?]?", input):
            output = re.search(r"^.*[Ww]hat does (?:the idiom )?\"(.*?)\" mean[.?]?", input)
            # Query idiom db and get the definition
            idiom = output.group(1)
            definition = self.find_best_definition(idiom)
            if definition in [None, ""]:
                return "Hmm. I'm kind of stumped on that one. I guess try a different one."
            else:
                return f"Yeah, that means: {definition}."
        elif re.fullmatch(r"^.*[Ww]hat (?:are|is) the idiom(?:s)? in: ([\"]?.*?[\"]?[.?]?)", input):
            output = re.search(r"^.*[Ww]hat (?:are|is) the idiom(?:s)? in: (\"(.*?)\"[.?]?)", input)
            sentence = output.group(1)
            list_of_idioms = [x[0] for x in self.pick_out_idioms(sentence)]
            if len(list_of_idioms) != 0:
                response = f"I think the idiom{'s' if len(list_of_idioms) > 1 else ''} in the sentence you gave me {'are' if len(list_of_idioms) > 1 else 'is'}: "
                for i in range(len(list_of_idioms)):
                    if i < len(list_of_idioms) - 1:
                        response += list_of_idioms[i] + ", "
                    else:
                        response += ("and " if len(list_of_idioms) > 1 else "") + list_of_idioms[i] + "."
                return response
            else:
                return "Sorry, I couldn't find any idioms in that sentence."
        elif re.fullmatch(r"^.*[Rr]eplace the idioms in this sentence with their definition: ([\"]?.*?[\"]?[.?]?)", input):
            output = re.search(r"^.*[Rr]eplace the idioms in this sentence with their definition: (\"(.*?)\"[.?]?)", input)
            sentence = output.group(1)
            replaced_sentence = self.replace_idioms_with_definitions(sentence)
            replaced_sentence.replace("\"","")
            return f'Here\'s my best guess to replace your sentence: "{replaced_sentence}"'
        else:
            return "Yeah, I don't really get that. Maybe you can try asking me a question about an idiom?"