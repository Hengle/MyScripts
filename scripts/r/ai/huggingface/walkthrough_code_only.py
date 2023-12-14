# Copyright (c) 2022 Graphcore Ltd. All rights reserved.

# THIS FILE IS AUTOGENERATED. Rerun SST after editing source file: walkthrough.py

import contextlib
import io
import json
import os
import sys
from pathlib import Path

import datasets
import matplotlib.pyplot as plt
import numpy as np

# import optimum.graphcore as optimum_graphcore
import pandas as pd
import torch
import transformers
from scipy.special import softmax
from torchvision import transforms

# The `chest-xray-nihcc` directory is assumed to be in the pwd, but may be overridden by the environment variable `DATASETS_DIR`
dataset_rootdir = Path(os.environ.get("DATASETS_DIR", ".")) / "chest-xray-nihcc"

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--dataset-dir", default=dataset_rootdir)

args = parser.parse_args()

dataset_rootdir = Path(args.dataset_dir)

# Path to the extracted "images" directory
images_dir = dataset_rootdir / "images"

# Path to Data_Entry_2017_v2020.csv
label_file = dataset_rootdir / "Data_Entry_2017_v2020.csv"

data = pd.read_csv(label_file)

# Converts the format of each label in the dataframe from "LabelA|LabelB|LabelC"
# into ["LabelA", "LabelB", "LabelC"], concatenates the
# lists together and removes duplicate labels
unique_labels = np.unique(
    data["Finding Labels"].str.split("|").aggregate(np.concatenate)
).tolist()

print(f"Dataset contains the following labels:\n{unique_labels}")

label_index = {v: i for i, v in enumerate(unique_labels)}


def string_to_N_hot(string: str):
    true_index = [label_index[cl] for cl in string.split("|")]
    label = np.zeros((len(unique_labels),), dtype=float)
    label[true_index] = 1
    return label


data["labels"] = data["Finding Labels"].apply(string_to_N_hot)

metadata_file = images_dir / "metadata.jsonl"
if not metadata_file.is_file():
    data[["Image Index", "labels"]].rename(
        columns={"Image Index": "file_name"}
    ).to_json(images_dir / "metadata.jsonl", orient="records", lines=True)

sys.exit(0)

train_val_split = 0.05
dataset = datasets.load_dataset(
    "imagefolder",
    data_dir=images_dir,
)

split = dataset["train"].train_test_split(train_val_split)
dataset["train"] = split["train"]
dataset["validation"] = split["test"]

model_name_or_path = "google/vit-base-patch16-224-in21k"

feature_extractor = transformers.AutoFeatureExtractor.from_pretrained(
    model_name_or_path
)


class XRayTransform:
    """
    Transforms for pre-processing XRay data across a batch.
    """

    def __init__(self):
        self.transforms = transforms.Compose(
            [
                transforms.Lambda(lambda pil_img: pil_img.convert("RGB")),
                transforms.Resize(feature_extractor.size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=feature_extractor.image_mean, std=feature_extractor.image_std
                ),
                transforms.ConvertImageDtype(dtype=torch.float16),
            ]
        )

    def __call__(self, example_batch):
        example_batch["pixel_values"] = [
            self.transforms(pil_img) for pil_img in example_batch["image"]
        ]
        return example_batch


# Set the training transforms
dataset["train"].set_transform(XRayTransform())
# Set the validation transforms
dataset["validation"].set_transform(XRayTransform())


def batch_sampler(examples):
    pixel_values = torch.stack([example["pixel_values"] for example in examples])
    labels = torch.tensor([example["labels"] for example in examples])
    return {"pixel_values": pixel_values, "labels": labels}


print(data.head(10))

fig = plt.figure(figsize=(20, 15))

unique_labels = np.array(unique_labels)

convert_image_to_float = transforms.ConvertImageDtype(dtype=torch.float32)
for i, data_dict in enumerate(dataset["validation"]):
    if i == 12:
        break
    image = data_dict["pixel_values"]
    # Convert image to format supported by imshow
    image = convert_image_to_float(image)
    label = data_dict["labels"]
    ax = plt.subplot(3, 4, i + 1)
    ax.set_title(", ".join(unique_labels[np.argwhere(label).flatten()]))
    plt.imshow(image[0])  # Plot only the first channel as they are all identical

fig.tight_layout()

model = transformers.AutoModelForImageClassification.from_pretrained(
    model_name_or_path, num_labels=len(unique_labels)
)

ipu_config = optimum_graphcore.IPUConfig.from_pretrained("Graphcore/vit-base-ipu")

training_args = optimum_graphcore.IPUTrainingArguments(
    output_dir=".graphcore/vit-model",
    overwrite_output_dir=True,
    per_device_train_batch_size=1,
    per_device_eval_batch_size=1,
    dataloader_num_workers=8,
    dataloader_drop_last=True,
    num_train_epochs=3,
    seed=1337,
    logging_steps=50,
    save_steps=1000,
    remove_unused_columns=False,
    warmup_ratio=0.25,
    lr_scheduler_type="cosine",
    learning_rate=2e-4,
    ignore_data_skip=True,
)

metric_auc = datasets.load_metric("roc_auc", "multilabel")


def compute_metrics(p):
    preds = np.argmax(p.predictions, axis=1)

    pred_scores = softmax(p.predictions.astype("float32"), axis=1)
    auc = metric_auc.compute(
        prediction_scores=pred_scores, references=p.label_ids, multi_class="ovo"
    )["roc_auc"]
    return {"roc_auc": auc}


trainer = optimum_graphcore.IPUTrainer(
    model=model,
    ipu_config=ipu_config,
    args=training_args,
    train_dataset=dataset["train"],
    eval_dataset=dataset["validation"],
    compute_metrics=compute_metrics,
    tokenizer=feature_extractor,
    data_collator=batch_sampler,
)

last_checkpoint = None
if os.path.isdir(training_args.output_dir) and not training_args.overwrite_output_dir:
    last_checkpoint = transformers.trainer_utils.get_last_checkpoint(
        training_args.output_dir
    )

# Capture the command line output for plotting loss and learning rate
output = io.StringIO()

with contextlib.redirect_stdout(output):
    trainer.train(resume_from_checkpoint=last_checkpoint)

# Visualise a fragment of the raw output
print(output.getvalue()[:500])
print("...")
print(output.getvalue()[-500:])

# Put the trainer logs in a data frame
values = []
for line in output.getvalue().split("\n"):
    if len(line) > 3 and line[:3] == "{'l":
        values.append(json.loads(line.replace("'", '"')))
training_records = pd.DataFrame(values)
training_records.tail(5)

fig, axs = plt.subplots(2, 1)
training_records.plot(x="epoch", y="loss", ax=axs[0])
training_records.plot(x="epoch", y="learning_rate", ax=axs[1])
fig.set_size_inches(8, 8)
fig.tight_layout()

metrics = trainer.evaluate()
trainer.log_metrics("eval", metrics)
trainer.save_metrics("eval", metrics)

# Generated:2022-09-08T15:27 Source:walkthrough.py SST:0.0.8