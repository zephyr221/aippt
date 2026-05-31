# Teaching Golden Examples

Use this reference when planning or repairing intro teaching decks. It captures
the current gold-standard direction for "机器学习导论".

## Machine Learning Intro

Do not treat a machine learning intro as an algorithm list. The hard part is the
cognitive slope:

```text
why rules fail -> core vocabulary -> one worked example -> four learning
paradigms -> training/validation loop -> algorithm overview -> evaluation
metrics -> common mistakes and next steps
```

Use house-price prediction as the main throughline:

- Motivation: rules for every neighborhood, house age, and exception are hard
  to write by hand.
- Vocabulary: area, location, and age become input x; the model fθ predicts
  price ŷ; the loss J compares prediction with transaction price.
- Worked example: show data preparation, model setup, loss, and generalization.
- Learning paradigms: supervised learning uses labels, unsupervised learning
  discovers structure, semi/self-supervised learning creates or economizes
  supervision, and reinforcement learning optimizes action through reward.
- Validation: test on new listings, inspect error, and update data or features.
- Algorithm overview: use numbered cards for KNN, decision tree, SVM, and naive
  Bayes; explain when to use them instead of dumping formulas.
- Evaluation: use a comparison matrix for classification metrics, regression
  metrics, generalization checks, and business risk.
- Summary: students should be able to retell "data in, model predicts, error
  corrects" before learning algorithm names.

For an intro lecture with limited time, do not force an exercise or check page
unless the user explicitly asks. Prefer clear transitions:

```text
洞察：四个词讲清楚后，房价预测就从例子变成了一条可复用主线。
洞察：任务类型回答的是反馈信号来自哪里，不是先背算法名字。
```

The goal is not to make every page a proof. The goal is to make every page
carry a concrete teaching object: definition, relation, example, formula,
process, contrast, or misconception.

Recommended component rhythm:

```text
rich_cards -> concept_diagram -> example_walkthrough -> learning_modes ->
loop_flow -> numbered_cards -> compare_matrix -> summary
```
