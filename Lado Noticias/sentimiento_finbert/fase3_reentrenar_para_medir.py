# -*- coding: utf-8 -*-
"""
Fase 3: reentrenar FinBETO SOLO PARA MEDIR su calidad sobre noticias no vistas.

No reemplaza al modelo que usa el pipeline (el que genero checkpoint_finetuned.jsonl y
beto_oraciones_finetuned.csv) ni guarda los modelos entrenados: guarda solo las metricas.

Replica la configuracion de 03_finetuning.ipynb (tesis version 2.0):
  modelo de partida beto_further_pretrained/, 4 clases, max 128 tokens, 5 epocas, lote 32 (eval 64),
  lr 2e-5, warmup 10%, weight decay 0,01, perdida ponderada por clase, evaluacion por epoca y
  mejor epoca segun F1 macro en validacion, fp16.

Se entrena con el MISMO codigo sobre dos divisiones, para que la diferencia se deba a la division:
  dataset/     division original (por oracion; el 100% del test viene de noticias vistas en train)
  dataset_v2/  division nueva (por noticia, sin repetidos; preparar_dataset_v2.py)
y con varias semillas, porque el test es chico (~800 oraciones).

En dataset/ se informa ademas el F1 sobre el test sin las oraciones que tambien estan en train.

Salidas: resultados_fase3/<division>_seed<N>.json y resultados_fase3/resumen.csv

Uso (desde sentimiento_finbert/):  python fase3_reentrenar_para_medir.py [--seeds 42 1 2] [--divisiones dataset dataset_v2]
"""

import argparse
import inspect
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from torch.utils.data import Dataset
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer,
                          TrainingArguments, set_seed)

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO_PARTIDA = os.path.join(AQUI, "beto_further_pretrained")
SALIDA = os.path.join(AQUI, "resultados_fase3")
LABEL_MAP = {"POS": 0, "NEG": 1, "NEU": 2, "MIXTO": 3}
ID2LABEL = {v: k for k, v in LABEL_MAP.items()}
MAX_LEN = 128


class SentimentDataset(Dataset):
    def __init__(self, df, tok):
        self.textos, self.labels, self.tok = df["texto"].tolist(), df["label_id"].tolist(), tok

    def __len__(self):
        return len(self.textos)

    def __getitem__(self, i):
        enc = self.tok(self.textos[i], truncation=True, max_length=MAX_LEN, padding="max_length", return_tensors="pt")
        return {"input_ids": enc["input_ids"].squeeze(), "attention_mask": enc["attention_mask"].squeeze(),
                "labels": torch.tensor(self.labels[i], dtype=torch.long)}


def pesos_de_clase(division, device):
    d = os.path.join(AQUI, division)
    if os.path.exists(os.path.join(d, "class_weights.pt")):
        return torch.load(os.path.join(d, "class_weights.pt")).to(device)
    j = json.load(open(os.path.join(d, "class_weights.json"), encoding="utf-8"))
    return torch.tensor([j["pesos"][l] for l in j["orden_label_id"]], dtype=torch.float).to(device)


def metricas(y, p):
    f1c = f1_score(y, p, average=None, labels=[0, 1, 2, 3])
    return {"f1_macro": round(float(f1_score(y, p, average="macro")), 4),
            "accuracy": round(float(accuracy_score(y, p)), 4),
            **{f"f1_{ID2LABEL[i]}": round(float(f1c[i]), 4) for i in range(4)},
            "n": int(len(y))}


def correr(division, seed, device):
    set_seed(seed)
    d = os.path.join(AQUI, division)
    tr, va, te = (pd.read_csv(os.path.join(d, f"{s}.csv")) for s in ("train", "val", "test"))
    tok = AutoTokenizer.from_pretrained(MODELO_PARTIDA)
    modelo = AutoModelForSequenceClassification.from_pretrained(
        MODELO_PARTIDA, num_labels=4, id2label=ID2LABEL, label2id=LABEL_MAP, ignore_mismatched_sizes=True).to(device)
    w = pesos_de_clase(division, device)

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            out = model(**inputs)
            loss = nn.CrossEntropyLoss(weight=w)(out.logits, labels)
            return (loss, out) if return_outputs else loss

    def compute_metrics(ev):
        logits, labels = ev
        return {"f1_macro": f1_score(labels, np.argmax(logits, axis=-1), average="macro")}

    tmp = tempfile.mkdtemp(prefix=f"fase3_{division}_{seed}_", dir=os.environ.get("FASE3_TMP"))
    # Compatibilidad entre versiones de transformers: en 5.x "evaluation_strategy" pasa a
    # "eval_strategy" y el calentamiento del 10% se indica con warmup_steps=0.1 (fraccion).
    params = inspect.signature(TrainingArguments).parameters
    estr = "eval_strategy" if "eval_strategy" in params else "evaluation_strategy"
    warm = {"warmup_ratio": 0.1} if "warmup_ratio" in params else {"warmup_steps": 0.1}
    args = TrainingArguments(
        output_dir=tmp, num_train_epochs=5, per_device_train_batch_size=32, per_device_eval_batch_size=64,
        **{estr: "epoch"}, save_strategy="epoch", save_total_limit=1, load_best_model_at_end=True,
        metric_for_best_model="f1_macro", greater_is_better=True, learning_rate=2e-5, **warm,
        weight_decay=0.01, logging_steps=50, seed=seed, fp16=(device == "cuda"), report_to="none")
    kw = {"processing_class": tok} if "processing_class" in inspect.signature(Trainer).parameters else {"tokenizer": tok}
    trainer = WeightedTrainer(model=modelo, args=args, train_dataset=SentimentDataset(tr, tok),
                              eval_dataset=SentimentDataset(va, tok), compute_metrics=compute_metrics, **kw)
    t0 = time.time()
    trainer.train()
    minutos = round((time.time() - t0) / 60, 2)
    hist = [{"epoca": int(round(l["epoch"])), "val_f1_macro": round(l["eval_f1_macro"], 4), "val_loss": round(l["eval_loss"], 4)}
            for l in trainer.state.log_history if "eval_f1_macro" in l]

    pred = trainer.predict(SentimentDataset(te, tok))
    y, p = te["label_id"].values, np.argmax(pred.predictions, axis=-1)
    res = {"division": division, "seed": seed, "minutos": minutos, "historial_val": hist,
           "mejor_epoca": max(hist, key=lambda h: h["val_f1_macro"])["epoca"],
           "test": metricas(y, p),
           "matriz_confusion": confusion_matrix(y, p, labels=[0, 1, 2, 3]).tolist()}
    filtradas = te["texto"].isin(set(tr["texto"])).values
    if filtradas.any():
        res["test_sin_textos_de_train"] = metricas(y[~filtradas], p[~filtradas])
        res["test_solo_textos_de_train"] = metricas(y[filtradas], p[filtradas])
    shutil.rmtree(tmp, ignore_errors=True)
    del trainer, modelo
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1, 2])
    ap.add_argument("--divisiones", nargs="+", default=["dataset", "dataset_v2"])
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Dispositivo:", device, torch.cuda.get_device_name(0) if device == "cuda" else "")
    os.makedirs(SALIDA, exist_ok=True)
    filas = []
    for division in a.divisiones:
        for seed in a.seeds:
            print(f"\n=== {division} | semilla {seed} ===", flush=True)
            r = correr(division, seed, device)
            json.dump(r, open(os.path.join(SALIDA, f"{division}_seed{seed}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            f = {"division": division, "seed": seed, "mejor_epoca": r["mejor_epoca"], "minutos": r["minutos"],
                 **{f"test_{k}": v for k, v in r["test"].items()}}
            if "test_sin_textos_de_train" in r:
                f["test_sin_repetidos_f1_macro"] = r["test_sin_textos_de_train"]["f1_macro"]
                f["test_sin_repetidos_n"] = r["test_sin_textos_de_train"]["n"]
            filas.append(f)
            print(json.dumps(f, ensure_ascii=False), flush=True)
    R = pd.DataFrame(filas)
    R.to_csv(os.path.join(SALIDA, "resumen.csv"), index=False)
    print("\n", R.groupby("division")[["test_f1_macro", "test_accuracy"]].agg(["mean", "std"]).round(4).to_string())


if __name__ == "__main__":
    main()
