# Preparing UltraChat for fine-tuning

UltraChat is a general English conversation dataset. It can help fine-tune a compatible base model's conversational style; it does not contain this project's private company knowledge and does not update the model used by the live app on its own. The dataset card lists 207,865 `train_sft` examples and a 23,110-example `test_sft` split. The complete dataset download is about 1.6 GB before any extra training artifacts. [Dataset card](https://huggingface.co/datasets/HuggingFaceH4/ultrachat_200k)

From the `backend` directory, install the optional preparation dependency and create a small sample first:

```powershell
python -m pip install datasets
python scripts/prepare_ultrachat.py --limit 1000 --output data/ultrachat_sample.jsonl
```

To prepare all supervised fine-tuning examples, omit `--limit`:

```powershell
python scripts/prepare_ultrachat.py --output data/ultrachat_train.jsonl
```

The output is JSONL with a `messages` array per conversation, ready to feed to a trainer that supports chat messages. The script uses the `train_sft` split by default; `--split test_sft` prepares evaluation data. Do not train on the test split.

This step only prepares data. Fine-tuning requires a compatible model, a training recipe, and suitable accelerator hardware. In particular, this dataset does not make `baidu/ERNIE-5.5-Flash-Preview` practical to load on an ordinary CPU. After training, serve the resulting compatible model through an OpenAI-compatible endpoint and add that endpoint under **AI providers**; the existing app router can then use it for generated answers.
