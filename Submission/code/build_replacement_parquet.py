import re
from difflib import SequenceMatcher
from idiom_parser import *

import duckdb


SOURCE_PATH = "../data/idiom_repository_all.parquet"
OUTPUT_PATH = "../data/idiom_repository_replaced.parquet"

MISSING_REPLACEMENT = "an expression with no source definition available"

FALLBACK_REPLACEMENTS = {
    "abbot's priory": "a prison",
    "and crap": "and similar worthless things",
    "big brother": "an intrusive authority figure who watches and controls people",
    "average joe": "an ordinary person",
    "big ol'": "very big",
    "big ole": "very big",
    "bottle of dog": "newcastle brown ale",
    "butter face": "someone with an attractive body but an unattractive face",
    "caesar's wife": "someone who must be above suspicion",
    "chinese green": "a shade of green",
    "damon and pythias": "two extremely loyal friends",
    "dumb shit": "a very stupid person",
    "freudian slip": "an accidental remark that reveals hidden thoughts",
    "funny man": "a comedian",
    "green indigo": "a greenish dye or pigment",
    "god forbid": "I hope that does not happen",
    "god forfend": "I hope that does not happen",
    "god's acre": "a cemetery",
    "hens' teeth": "something extremely rare",
    "hobson's choice": "no real choice at all",
    "i never did": "I certainly did not",
    "i'd say": "I would agree",
    "i'll be": "I am surprised",
    "i'll be damned": "I am very surprised",
    "i'm a dutchman": "I would be extremely surprised",
    "i'm all right, jack": "I only care about my own situation",
    "indian summer": "an unseasonably warm period late in the year",
    "itsy bitsy": "very small",
    "itty bitty": "very small",
    "jack tar": "a sailor",
    "jekyll and hyde": "someone with two sharply different sides",
    "ladies' man": "a man who is very attractive to women",
    "light skirt": "a sexually promiscuous woman",
    "loved up": "feeling very affectionate and happy",
    "lucky duckling": "a very lucky person",
    "muckety muck": "an important or powerful person",
    "na-na na-na na-na": "a mocking taunt",
    "number 11": "the treasury of the united kingdom",
    "number eleven": "the treasury of the united kingdom",
    "occam's razor": "the simplest explanation is usually best",
    "pandora's box": "a source of many unexpected troubles",
    "scout's honor": "I promise honestly",
    "a new york minute": "a very short moment",
    "a pyrrhic victory": "a victory won at too great a cost",
    "a trojan horse": "something dangerous disguised as harmless",
    "a back-seat driver": "someone who gives unwanted advice",
    "a big cheese": "an important person",
    "a big gun": "an important or influential person",
    "a big shot": "an important person",
    "a big wheel": "an important person",
    "a bird in the hand": "something you already have for certain",
    "a bitter pill": "an unpleasant fact or situation to accept",
    "a black sheep": "a disreputable member of a group or family",
    "a blind spot": "an area of weakness or ignorance",
    "a class act": "an excellent and impressive person or thing",
    "a clean bill of health": "confirmation that everything is fine",
    "a closed book": "something or someone that is hard to understand",
    "a dark horse": "an unexpected winner or contender",
    "a dead cat bounce": "a brief recovery during an overall decline",
    "a dog's breakfast": "a complete mess",
    "a dog's life": "a miserable existence",
    "a double-edged sword": "something that brings both benefits and harm",
    "a doubting thomas": "a habitually skeptical person",
    "a drop in a bucket": "a very small amount",
    "a fair-weather friend": "a friend only in good times",
    "a false dawn": "an early sign of success that does not last",
    "a grey area": "something unclear or hard to classify",
    "a hidden agenda": "a secret motive",
    "a hornet's nest": "a source of trouble or conflict",
    "a king's ransom": "a huge amount of money",
    "a loose cannon": "an unpredictable person",
    "a losing battle": "a struggle that is unlikely to succeed",
    "a lump in your throat": "a feeling of strong emotion that makes speaking hard",
    "a means to an end": "something useful only for reaching another goal",
    "a millstone round your neck": "a heavy burden",
    "a mixed blessing": "something with both advantages and disadvantages",
    "a moot point": "a point that is uncertain or no longer worth arguing",
    "a new lease of life": "renewed energy or opportunity",
    "a paper tiger": "something that seems threatening but is actually weak",
    "a poisoned chalice": "an apparent benefit that brings trouble",
    "a pretty penny": "a large amount of money",
    "a red herring": "a misleading clue or distraction",
    "a safe pair of hands": "a reliable person",
    "a silver lining": "a hopeful aspect of a bad situation",
    "a slippery slope": "a situation likely to worsen step by step",
    "a stab in the dark": "a guess made with little information",
    "a sticky wicket": "a difficult situation",
    "a straw in the wind": "an early sign of future change",
    "a tower of strength": "a very reliable source of support",
    "arrow of time": "the one-way progression of time",
    "be in like flynn": "be in a very favorable position",
    "before you can say knife": "very quickly",
    "bite off more than you can chew": "take on more than you can handle",
    "bone to pick": "a complaint to discuss",
    "bring something home to someone": "make someone fully understand something",
    "diamond cuts diamond": "equally clever people can match each other",
    "do a moonlight flit": "leave secretly to avoid responsibilities",
    "drop a clanger": "make an embarrassing mistake",
    "drop your aitches": "leave out the h sound when speaking",
    "eat, sleep and breathe something": "be completely absorbed in something",
    "famous for fifteen minutes": "briefly famous",
    "get your just deserts": "receive the punishment you deserve",
    "against your better judgement": "despite knowing better",
    "give someone the bum's rush": "force someone to leave quickly",
    "give a tongue-lashing": "scold harshly",
    "have a plum in your mouth": "speak with an affected upper-class accent",
    "in dire straits": "in serious trouble",
    "in full flow": "moving or progressing strongly and continuously",
    "it'll be a frosty friday in july": "it will never happen",
    "kiss someone's arse": "flatter someone in a servile way",
    "knock someone sideways": "shock or overwhelm someone",
    "lead someone up the garden path": "mislead someone",
    "like a hen with one chick": "overly protective",
    "make common cause with": "join forces with",
    "the small hours": "very late at night",
    "of the old school": "traditional in style or thinking",
    "heart misses a beat": "feel a sudden shock or excitement",
    "hit the mark": "be accurate or successful",
    "sleep on it": "wait before deciding",
    "on shanks's pony": "on foot",
    "on the pig's back": "in a very favorable situation",
    "overstep the mark": "go too far",
    "painting the forth bridge": "doing endless repetitive work",
    "play merry hell with": "cause serious trouble for",
    "play a blinder": "perform extremely well",
    "place in the sun": "a desirable position or opportunity",
    "put your heads together": "think about something together",
    "pull one's punches": "hold back and act less forcefully than possible",
    "quick as a flash": "extremely quickly",
    "rare animal": "an unusual person or thing",
    "richard roe": "a generic placeholder person",
    "ride it out": "endure something until it ends",
    "root around": "search around",
    "run rings round": "easily outperform",
    "safety in numbers": "being in a group makes you safer",
    "scare the daylights out of": "frighten very badly",
    "show your teeth": "show aggression or determination",
    "shed find": "an old item rediscovered in storage",
    "screaming abdabs": "severe nervousness or panic",
    "spic and span": "very clean and tidy",
    "spick and span": "very clean and tidy",
    "start the ball rolling": "begin the process",
    "still waters run deep": "quiet people often have deep thoughts or feelings",
    "stick in your gizzard": "be very hard to accept",
    "sugar coated": "made to seem better than it really is",
    "take the easy way out": "choose the simplest but less courageous option",
    "teensy weensy": "very small",
    "teeny weeny": "very small",
    "teething problems": "minor early problems",
    "that figures": "that makes sense",
    "the awkward age": "adolescence",
    "the genuine article": "the real thing",
    "the matthew principle": "advantages tend to accumulate to those who already have them",
    "the pen is mightier than the sword": "words and ideas are more powerful than violence",
    "the upper crust": "the highest social class",
    "the wide blue yonder": "the far open distance",
    "till the cows come home": "for a very long time",
    "time is money": "time is valuable",
    "top cat": "the person in charge",
    "topsy turvy": "in a confused or disordered state",
    "to err is human, to forgive divine": "making mistakes is human, but forgiving is nobler",
    "trailer park trash": "an insulting term for someone seen as poor and low-class",
    "un-rock and roll": "not cool or exciting",
    "weak at the knees": "overwhelmed by emotion or desire",
    "when it comes to the crunch": "when the decisive moment arrives",
    "who goes there?": "identify yourself",
    "whomp on": "hit repeatedly",
    "wouldn't you know": "that is just what you would expect",
    "wrap someone round your little finger": "control someone easily",
    "pull the strings": "secretly control events",
    "all the while": "throughout that whole time",
    "see sense": "act reasonably",
    "not turn a hair": "stay completely calm",
    "die like flies": "die in large numbers",
    "fly high": "be very successful or ambitious",
    "olive branch": "gesture of peace or reconciliation",
    "punch line": "final joke or key point",
    "what's cooking": "what is happening",
    "have a silver tongue": "speak very persuasively",
    "strike at the root of": "attack the fundamental cause of",
    "over the odds": "more than expected or reasonable",
    "spill the beans": "reveal a secret",
    "keep your nose to the grindstone": "work steadily and hard",
    "a wild goose chase": "a pointless search",
    "it stands to reason": "it is logically obvious",
    "ray of sunshine": "cheerful person",
    "show your teeth": "show aggression or determination",
    "have an axe to grind": "have a selfish motive",
    "one's number is up": "someone's end or defeat is imminent",
    "poke fun at": "make fun of",
    "know the ropes": "know how things work",
    "seeing is believing": "direct evidence is convincing",
    "sail through": "succeed easily",
    "hands up": "I admit it",
    "make whoopee": "celebrate noisily",
    "rough diamond": "good person with rough manners",
}

PREFERRED_REPLACEMENTS = {
    "bottle of dog": "newcastle brown ale",
    "hell if i know": "I have no idea",
    "up with the larks": "awake very early",
}

DATEISH_TOKENS = {
    "mid",
    "early",
    "late",
    "century",
    "century?",
    "c.",
    "ca.",
    "circa",
}

REFERENCE_JOINERS = re.compile(r"\s*(?:,|;|/| and | or )\s*")
REFERENCE_PREFIX = re.compile(
    r"^(?:see|synonym of|alternative form of|alternative spelling of|euphemistic form of)\s+",
    flags=re.I,
)
TEMPLATE_ARTIFACTS = re.compile(r"\b(?:lang|of)=[a-z-]+\b", flags=re.I)
STOPWORDS = {
    "a",
    "an",
    "the",
    "of",
    "to",
    "and",
    "or",
    "in",
    "on",
    "at",
    "for",
    "with",
    "from",
}


def is_missing(value: object) -> bool:
    if value is None:
        return True
    return isinstance(value, float) and value != value


def normalize_lookup(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[\"“”]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .")


def is_dateish(token: str) -> bool:
    token = token.strip(".,;:!?()[]{}")
    if not token:
        return False
    lower = token.lower()
    if lower in DATEISH_TOKENS:
        return True
    if re.fullmatch(r"\d{1,4}(?:st|nd|rd|th)?(?:-\d{1,4}(?:st|nd|rd|th)?)?", lower):
        return True
    if re.fullmatch(r"\d{3,4}s(?:-\d{2,4}s?)?", lower):
        return True
    return False


def strip_defdate_prefix(text: str) -> str:
    lower = text.lower()
    if not lower.startswith("defdate."):
        return text

    remainder = text[len("defdate.") :].strip()
    tokens = remainder.split()
    while tokens and is_dateish(tokens[0]):
        tokens.pop(0)
    return " ".join(tokens).strip()


def clean_definition_text(text: str) -> str:
    if is_missing(text):
        return ""

    text = str(text).strip()
    if not text:
        return ""

    text = text.replace("’", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"^(?:non-gloss definition|n-g|en-definition)\s+", "", text, flags=re.I)
    text = strip_defdate_prefix(text)
    text = re.sub(r"^te\b", "to", text, flags=re.I)
    text = re.sub(r"^w[:\s]+", "", text, flags=re.I)
    text = re.sub(r"^a,\s*", "a ", text, flags=re.I)
    text = re.sub(r"\.(?:lang|of)=en\b", "", text, flags=re.I)
    text = TEMPLATE_ARTIFACTS.sub("", text)
    text = re.sub(r"\b[a-z-]+=", "", text, flags=re.I)
    text = re.sub(r"\blang=en\b", "", text, flags=re.I)
    text = re.sub(r"\bof=en\b", "", text, flags=re.I)
    text = text.replace("of=", " ")
    text = re.sub(r"\bfrankfurterhot dog\b", "frankfurter or hot dog", text, flags=re.I)
    text = re.sub(r"\bw mash\b", "Monster Mash", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" .;")


def polish_replacement(text: str, pos: str | None) -> str:
    text = clean_definition_text(text)
    if not text:
        return ""

    pos = "" if is_missing(pos) else str(pos).strip().lower()
    if pos in {"verb", "phrase"}:
        text = re.sub(r"^to\s+", "", text, flags=re.I)

    text = re.sub(r"\s+", " ", text)
    return text.strip(" .;")


def extract_references(text: str) -> list[str]:
    body = REFERENCE_PREFIX.sub("", text).strip(" .;:")
    body = TEMPLATE_ARTIFACTS.sub("", body)
    body = re.sub(r"\b(?:lang|of)=en\b", "", body, flags=re.I)
    body = body.replace("of=", " ")
    candidates = []
    for part in REFERENCE_JOINERS.split(body):
        part = re.sub(r"^(?:something|someone)\s+", "", part, flags=re.I)
        part = part.strip(" .;:")
        if part:
            candidates.append(part)
    return candidates


def tokenize_lookup(text: str) -> list[str]:
    return [token for token in normalize_lookup(text).split() if token]


def extract_gloss_from_template(text: str) -> str:
    cleaned = clean_definition_text(text)
    paren_match = re.search(r"\(([^()]+)\)\s*$", cleaned)
    if paren_match:
        return paren_match.group(1).strip(" .;")

    if ":" not in cleaned:
        return ""

    gloss = cleaned.split(":", 1)[1].strip()
    if not gloss:
        return ""
    if len(gloss.split()) < 2 and normalize_lookup(gloss) in {"a", "an", "the"}:
        return ""
    return gloss


def has_template_noise(text: str) -> bool:
    normalized = normalize_lookup(text)
    return (
        "lang en" in normalized
        or normalized.startswith("synonym")
        or normalized.startswith("alternative")
        or normalized in {"related to don't", "related to with the"}
    )


def score_reference_candidate(reference: str, source_idiom: str, candidate_idiom: str) -> float:
    ref_tokens = [token for token in tokenize_lookup(reference) if token not in STOPWORDS]
    source_tokens = set(tokenize_lookup(source_idiom))
    candidate_tokens = set(tokenize_lookup(candidate_idiom))

    score = SequenceMatcher(None, normalize_lookup(source_idiom), normalize_lookup(candidate_idiom)).ratio()
    if ref_tokens:
        overlap = sum(1 for token in ref_tokens if token in candidate_tokens)
        score += overlap * 0.35
        if overlap == len(ref_tokens):
            score += 0.4

    for token in source_tokens:
        if token.isdigit() and token in candidate_tokens:
            score += 0.5

    return score


def find_reference_matches(
    reference: str,
    source_idiom: str,
    by_idiom: dict[str, list[int]],
    rows: list[dict],
) -> list[int]:
    normalized_reference = normalize_lookup(reference)
    if normalized_reference in by_idiom:
        return by_idiom[normalized_reference]

    matches: list[tuple[float, int]] = []
    for index, row in enumerate(rows):
        candidate_idiom = row["idiom"]
        score = score_reference_candidate(reference, source_idiom, candidate_idiom)
        if score >= 1.15:
            matches.append((score, index))

    matches.sort(reverse=True)
    return [index for _, index in matches[:5]]


def make_missing_replacement(idiom: str) -> str:
    normalized = normalize_lookup(idiom)
    if normalized in FALLBACK_REPLACEMENTS:
        return FALLBACK_REPLACEMENTS[normalized]
    if normalized.startswith("wiktionary:"):
        return "a Wiktionary archive or maintenance page"
    if normalized.startswith(("a ", "an ", "the ")):
        return "something with no source definition available"
    if normalized.startswith(
        ("in ", "on ", "at ", "by ", "for ", "from ", "with ", "under ", "over ", "between ")
    ):
        return "in an unspecified figurative way"
    return MISSING_REPLACEMENT


def build_replacements(rows: list[dict]) -> list[str]:
    by_idiom: dict[str, list[int]] = {}
    for index, row in enumerate(rows):
        by_idiom.setdefault(normalize_lookup(row["idiom"]), []).append(index)

    cache: dict[int, str] = {}

    def resolve(index: int, seen: set[int]) -> str:
        if index in cache:
            return cache[index]
        if index in seen:
            return make_missing_replacement(rows[index]["idiom"])

        seen = set(seen)
        seen.add(index)

        row = rows[index]
        definition = clean_definition_text(row.get("definition"))
        replacement = ""

        if definition:
            if REFERENCE_PREFIX.match(definition):
                gloss = extract_gloss_from_template(definition)
                if gloss:
                    replacement = polish_replacement(gloss, row.get("pos"))

                for reference in extract_references(definition):
                    if replacement and replacement != MISSING_REPLACEMENT:
                        break
                    reference_key = normalize_lookup(reference)
                    match_indexes = by_idiom.get(reference_key, [])
                    if not match_indexes:
                        match_indexes = find_reference_matches(reference, row["idiom"], by_idiom, rows)

                    for match_index in match_indexes:
                        replacement = resolve(match_index, seen)
                        if replacement and replacement != MISSING_REPLACEMENT:
                            break
                    if replacement and replacement != MISSING_REPLACEMENT:
                        break
                if not replacement:
                    replacement = f"related to {extract_references(definition)[0]}" if extract_references(definition) else ""
            else:
                replacement = polish_replacement(definition, row.get("pos"))

        if not replacement:
            replacement = make_missing_replacement(row["idiom"])
        elif has_template_noise(replacement):
            replacement = make_missing_replacement(row["idiom"])

        preferred = PREFERRED_REPLACEMENTS.get(normalize_lookup(row["idiom"]))
        if preferred:
            replacement = preferred

        cache[index] = replacement
        return replacement

    return [resolve(index, set()) for index in range(len(rows))]

def addCanonicalVariation():
    query = f"""
        CREATE TABLE
            idioms
        AS (
            SELECT *
            FROM '{SOURCE_PATH}'
        )
    """

    duckdb.query(query)

    df = duckdb.query("SELECT * FROM idioms").df()

    IdiomParser = Idioms()

    for _, row in df.iterrows():
        idiom = row["idiom"]
        variations = list(row["variations"])

        singular_idiom = IdiomParser.reduce_single_present_tense(idiom)

        if (idiom.lower() != singular_idiom.lower()):
            query = f"""
                UPDATE
                    idioms
                SET
                    variations = ?
                WHERE
                    idiom = ?
            """
            duckdb.query(query, params=[variations + [singular_idiom], idiom])

    duckdb.query(f"COPY (SELECT * FROM idioms) TO '{OUTPUT_PATH}' (FORMAT parquet)")


def main() -> None:
    con = duckdb.connect()
    df = con.execute(f"SELECT * FROM read_parquet('{SOURCE_PATH}')").fetchdf()
    rows = df.to_dict("records")
    df["replacement"] = build_replacements(rows)

    con.register("idiom_replacements_df", df)
    con.execute(
        f"""
        COPY idiom_replacements_df
        TO '{OUTPUT_PATH}'
        (FORMAT PARQUET)
        """
    )

    addCanonicalVariation()

    print(f"Wrote {len(df)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
