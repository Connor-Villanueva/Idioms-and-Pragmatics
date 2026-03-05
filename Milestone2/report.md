# Project Milestone 2 - Idioms and Pragmatics

Jazzy De Los Santos, Timothy Matthies, Connor Villanueva

## Current State of Project

Currently, 2 main tasks have been completed for our project.

1. **Convert JSON repository of idioms into an easily queryable Parquet.**

    As is, the given JSON repository of idioms was annoying to deal with. There were nested JSON objects and many, meaningless, nested arrays. See below for an example:

    ```
    {
        "variations": [],
        "idiom": "23 Skidoo Street",
        "sources": [
        "Wiktionary"
        ],
        "entry": [
        {
            "usages": [
            [
                "\"apply at once to xyz, 23 skidoo st., new york.\"",
                "olive oyl: 23 skidoo street, driver."
            ]
            ],
            "definition": "defdate. 1900 a fictitious place or a generic place that could refer to any location.",
            "pos": "proper noun"
        }
        ],
        "id": 8,
        "confidence": 1
    }
    ```

    To put this into an easier format, we created the following script to convert each JSON object into Python dictionary objects. We then create a Pandas Dataframe from these dictionaries, and write the result to a parquet file.

    ```
    with open(DATA_PATH, "rt", encoding="utf8") as f:
        data = json.load(f)

    df_raw = []

    for i in range(len(data)):
        tmp = {}
        idiom = data[i]

        idiom_keys = idiom.keys()
        
        for ikey in idiom_keys:
            d1 = idiom[ikey]

            if (isinstance(d1, list)):
                # Lists can have a dictionary inside of them
                if (len(d1) > 0 and isinstance(d1[0], dict)):
                    d2 = d1[0]
                    # There could be more than one dictionary...
                    for ekey in d2.keys():
                        if (isinstance(d2[ekey], list)):
                            tmp[ekey] = d2[ekey][0]
                        else:
                            tmp[ekey] = d2[ekey]

                elif (len(d1) > 0 and isinstance(d1[0], list)):
                    print(ikey, d1[0])

                else:
                    tmp[ikey] = d1

            elif (isinstance(d1, str)):
                tmp[ikey] = d1
            elif (isinstance(d1, int)):
                tmp[ikey] = d1

        df_raw.append(tmp)

    df = pd.DataFrame(df_raw)
    df.to_parquet("../Data/idiom_repository_all.parquet")
    ```


2. **Began a basic tagging process using Spacy PhraseMatcher.**

    With the data now in a format that is easier to work with, we wanted to try identifying the occurence of idioms in sentences. To do this, we collected all variations of the idioms we have and used Spacy's PhraseMatcher. Below is the following code for this process:

    ```
    query = f"""
        (SELECT 
            TRIM(variations, '[""]') AS all_variations
        FROM
            '{DATA_PATH}'
        WHERE
            len(variations) > 2)
        UNION
        (SELECT
            idiom
        FROM
            '{DATA_PATH}'
        )
    """
    df = duckdb.query(query).df()

    nlp = spacy.load("en_core_web_sm")
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(p) for p in df["all_variations"].values]

    matcher.add("PHRASES", patterns)
    ```

    Now given a document, we can use the matcher to identify the occurence of idioms. Below is a test we used and the results of the test:

    ```
    doc = nlp(
    """
    We tried to keep the party a surprise, but Sam let the cat out of the bag.
    I can kill two birds with one stone by stopping at the post office on my way to work.
    That guy was so gone, he was two sheets to the wind. 
    The bar was so crazy it was a free-for-all. 
    Make 'er indoors get us a couple of sandwiches.
    """)


    # -------- RESULTS --------

    Match ID             | Text                           | Start | End  
    --------------------------------------------------------------------
    1303609015319360366  | let the cat out of the bag     | 12    | 19   
    1303609015319360366  | kill two birds with one stone  | 23    | 29   
    1303609015319360366  | two birds with one stone       | 24    | 29   
    1303609015319360366  | free-for-all                   | 65    | 70   
    1303609015319360366  | 'er indoors                    | 73    | 76
    ```


    These results tell us the idiom that was found and the start and end position of that idiom in the given document string. While this is a really good start, this actually gives us some useful information to use in this next week. For starters, the database does not have enough variations of some idioms. For example, `free-for-all` will not get detected if it were in the text as `free for all`. Simple things like this are easy to fix by adding another variation to the idiom in the database.

    Another issue we will have is that by doing phrase matching like this, we are requiring that the entire phrase be inside a given sentence with no interuptions. If a phrase were to be interupted in text by a name or something else, then this phrase matcher would not find it. This is problematic because we want to be able to use this in sentences that may occur in every day speech.

    Despite these problems, this is really good place for us to start as it gives us a good understanding of what to do next.
    