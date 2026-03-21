from idiom_parser import *
from random import sample, seed

idiomatic_sentences = None
non_idiomatic_sentences = None

# Load sentences with non-dioms
with open("../data/non-idioms.txt") as non_idioms_file:
    non_idiomatic_sentences = [(x.strip(), False) for x in non_idioms_file if x.strip()]

# Larger # of idiom sentences, so sample same length as non-idioms
with open("../data/theidioms_sentences.txt") as idioms_file:
    idiomatic_sentences = [(x.strip(), True) for x in idioms_file if x.strip()]
    seed(24)
    idiomatic_sentences = sample(idiomatic_sentences, len(non_idiomatic_sentences))

all_sentences = idiomatic_sentences + non_idiomatic_sentences

parser = Idioms()
results = [(x[0], x[1], False if len(parser.pick_out_idioms(parser.reduce_single_present_tense(x[0]))) == 0 else True) for x in all_sentences]

true_pos, false_pos, true_neg, false_neg = 0, 0, 0, 0

for result in results:
    if result[1] == True:
        if result[2] == True:
            true_pos += 1
        else:
            false_pos += 1

    else:
        if result[2] == False:
            true_neg += 1
        else:
            false_neg += 1

accuracy = (true_neg + true_pos) / (true_pos + true_neg + false_neg + false_pos)
precision = (true_pos) / (true_pos + false_pos)
recall = (true_pos) / (true_pos + false_neg)
f1 = 2*(precision * recall) / (precision + recall)

print(f"\n-=-=-=-=- Start Eval Metrics -=-=-=-=-")
print(f"Accuracy: {accuracy:.4f}")
print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1: {f1:.4f}")
print(f"-=-=-=-=- End Eval Metrics -=-=-=-=-\n")