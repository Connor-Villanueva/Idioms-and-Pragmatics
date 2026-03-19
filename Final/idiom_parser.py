import spacy
from spacy.matcher import PhraseMatcher
import nltk
import re
from rapidfuzz import fuzz
import duckdb as dd

DATA_PATH = "./Data/idiom_repository_all.parquet"

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

    def pick_out_idioms(self, input: str):
        doc = self.nlp(input)
        matches = self.matcher(doc)
        return [doc[start: end].text for _, start, end in matches]

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
            list_of_idioms = self.pick_out_idioms(sentence)
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

        else:
            return "Yeah, I don't really get that. Maybe you can try asking me a question about an idiom?"