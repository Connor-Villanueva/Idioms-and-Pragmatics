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
DATA_PATH = os.path.abspath(os.path.join(BASE_DIR, "../Data/idiom_repository_final.parquet"))

class Idioms():
    def __init__(self):
        self.idiom_df = dd.query(f"""
            SELECT definition, CAST(variations AS VARCHAR[]) || [idiom] AS all_variations, replacement
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
                self.phrase_to_definition[self.normalize(phrase)] = row["definition"] if type(row["definition"]) != float else row["replacement"]

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
    
    def reduce_single_present_tense(self, sentence: str):
        sentence = sentence.replace('"', '')
        doc = self.nlp(sentence)

        new_tokens = []

        for token in doc:
            if (token.pos_ == "VERB" or token.pos_ == "AUX"):

                if (token.tag_ in ["VBD", "VBG", "VBN", "VBP"]):
                    new_tokens.append(token.lemma_ if token.lemma_ != "be" else "is")
                else:
                    new_tokens.append(token.text)

            elif (token.pos_ == "NOUN"):
                new_tokens.append(token.lemma_)

            else:
                new_tokens.append(token.text)
        res = " ".join(new_tokens)

        res = re.sub(r' \'', r"'", res)
        res = re.sub(r' \.', r'.', res)
        res = re.sub(r' - ', r'-', res)
        res = re.sub(r' , ', r', ', res)
        
        return res
    
    def llm_fix_grammar(self, sentence, idiom_matches):
        for match in idiom_matches:
            idiom = match["text"]
            definition = match["definition"]

            prompt = f"""
            Original sentence: "{sentence}"
            Replace the phrase "{idiom}" with the definition "{definition}".
            Rewrite the sentence so that it is grammatically perfect and natural.
            You may correct punctuation and capitalization in the definition.
            Do not edit the non-idiom part unless it is for grammar.
            Only return the corrected sentence. No explanation.
            """

            res = requests.post("http://localhost:11434/api/generate",
                                    json={
                                        "model": "llama3",
                                        "prompt": prompt,
                                        "stream": False
                                    })
            
            print(f"LLM Status Code: {res.status_code}")
            if (res.status_code == 200):
                sentence = res.json()["response"].strip()
            
        return sentence

    def replace_idioms_with_definitions(self, text: str) -> str:
        matches = self.find_idiom_matches(text)

        if (len(matches) > 0):
            res = self.llm_fix_grammar(text, matches)

            if (res != text):
                print("LLM Generated Sentence")
                return res
            
            print("No LLM Response. Replacing normally...")
            for match in reversed(matches):
                text = text[:match["start"]] + match["definition"] + text[match["end"]:]
            return text
    
        return None
    
    def fix_response_input(self, sentence: str):
        try:
            question, idiom_sent = sentence.split(":")

            idiom_sent = idiom_sent.replace('"', "")
            cleaned_sent = self.reduce_single_present_tense(idiom_sent)
            cleaned_input = question + ': "' + cleaned_sent.strip() + '"'

            matches = self.pick_out_idioms(cleaned_input)

            tokens = nltk.word_tokenize(sentence)
            for match in matches:
                idiom, start, end = match

                idiom_tokens = nltk.word_tokenize(idiom)

                for i, j in enumerate(range(start, end)):
                    tokens[j] = idiom_tokens[i]
                
            sentence = " ".join(tokens)
            sentence = re.sub(r' ``', r'', sentence)
            sentence = re.sub(r' \'\'', r'', sentence)

            question, idiom_sent = sentence.split(":")

            # cleaned_sent = self.reduce_single_present_tense(idiom_sent)
            cleaned_input = question.strip() + ': "' + idiom_sent.strip() + '"'

            return cleaned_input

        except Exception as e:
            return None
        
    def respond(self, input: str) -> str:
        cleaned_input = self.fix_response_input(input)

        if (cleaned_input is None):
            cleaned_input = input

        if re.fullmatch(r"^.*[Dd]o you love me[.?]?", input):
            return "No, I only love idioms and you'll never be them."
        elif re.fullmatch(r"^.*[Ww]hat does (?:the idiom )?([\"]?.*?[\"]?) mean[.?]?", cleaned_input):
            output = re.search(r"^.*[Ww]hat does (?:the idiom )?\"(.*?)\" mean[.?]?", cleaned_input)
            # Query idiom db and get the definition
            idiom = output.group(1)
            definition = self.find_best_definition(idiom)
            if definition in [None, ""]:
                return "Hmm. I'm kind of stumped on that one. I guess try a different one."
            else:
                return f"Yeah, that means: {definition}."
        elif re.fullmatch(r"^.*[Ww]hat (?:are|is) the idiom(?:s)? in: ([\"]?.*?[\"]?[.?]?)", cleaned_input):
            output = re.search(r"^.*[Ww]hat (?:are|is) the idiom(?:s)? in: (\"(.*?)\"[.?]?)", cleaned_input)
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
        elif re.fullmatch(r"^.*[Rr]eplace the idioms in this sentence with their definition: ([\"]?.*?[\"]?[.?]?)", cleaned_input):
            output = re.search(r"^.*[Rr]eplace the idioms in this sentence with their definition: (\"(.*?)\"[.?]?)", cleaned_input)
            sentence = output.group(1)
            replaced_sentence = self.replace_idioms_with_definitions(sentence)

            if (replaced_sentence is None):
                return f'I don\'t quite understand the idiom in the sentence: {input.split(":")[1]}'
            return f'Here\'s my best guess to replace your sentence: {replaced_sentence}'
        else:
            return "Yeah, I don't really get that. Maybe you can try asking me a question about an idiom?"