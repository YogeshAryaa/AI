# Preparing OpenAssistant OASST1 for fine-tuning

OASST1 is a human-generated, human-reviewed conversation dataset with messages stored as parent-linked trees. The app does not train on it during chat. This utility filters deleted and negatively reviewed messages, optionally filters by language, reconstructs each assistant leaf's conversation path, and writes chat-message JSONL for a separate fine-tuning job. The dataset has an Apache-2.0 license; review its card and attribution requirements before redistributing trained artifacts. [Dataset card](https://huggingface.co/datasets/OpenAssistant/oasst1)

From the `backend` directory, install optional data-reading dependencies and prepare a small English sample:

```powershell
python -m pip install pandas pyarrow huggingface_hub
python scripts/prepare_oasst1.py --limit 1000 --output data/oasst1_sample.jsonl
```

The command reads the Hugging Face parquet URI directly, following the provided `pd.read_parquet("hf://datasets/...")` pattern. Omit `--limit` for the full split. `--split validation` prepares validation data; `--language all` includes all available languages. Keep validation examples out of training.

The generated file is training data, not an inference-time knowledge base. It can teach a compatible model conversational patterns, but does not add company facts or update the live model automatically. Fine-tune a suitable model separately, serve it through an OpenAI-compatible endpoint, and add that endpoint under **AI providers** to use it for answers.
