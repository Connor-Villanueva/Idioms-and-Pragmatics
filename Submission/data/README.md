# Idiom Repository Updates

Initially we were given a JSON document that was created by a previous graduate student. This student collected nearly 10,000 idioms. We have made some changes to this repository to both expand on their work and provide usefulness for our own project.

1. We have converted the JSON document in Parquet for easier querying using DuckDB or Pandas.

2. Some definitions were missing. An additional `replacement` field was added with a fallback definition for these cases.

3. Some variations were added to idioms. These variations are the canonical form of the idioms (i.e. singular and present tense).