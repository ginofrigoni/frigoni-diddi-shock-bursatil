# -*- coding: utf-8 -*-
"""
Entrenamiento de FinBETO con 3 clases (tesis versión 6.0). Fase 3 de CRISP-DM (preparación).

Misma configuracion que la 5.0 (y que 03_finetuning.ipynb de la 2.0), salvo el numero de clases:
  modelo de partida modelos/beto_further_pretrained/, 3 clases (POS, NEG, NEU; MIXTO paso a NEU),
  max 128 tokens, 5 epocas, lote 32 (eval 64), lr 2e-5, warmup 10%, weight decay 0,01, perdida
  ponderada por clase, evaluacion por epoca y mejor epoca segun F1 macro en validacion, fp16.

Division: salidas/dataset_3clases/ (por noticia; preparar_dataset_v2.py).
Se entrena con varias semillas porque el test es chico (786 oraciones): se informa media y desvio.
El modelo de la semilla 42 se GUARDA en modelos/beto_finetuned_3clases/ y es el que clasifica
el corpus completo (en la 5.0 el modelo final no habia quedado guardado).

Salidas:
  salidas/entrenamiento/seed<N>.json                   historial, metricas de test, matriz de confusion
  salidas/entrenamiento/predicciones_test_seed42.csv   texto, etiqueta y prediccion (para los ejemplos)
  salidas/entrenamiento/resumen.csv
  modelos/beto_finetuned_3clases/                      el modelo final (no va a GitHub)

Uso:  python fase3_reentrenar_para_medir.py [--seeds 42 1 2] [--guardar-seed 42]
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
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score
from torch.utils.data import Dataset
from transformers import (AutoModelForSequenceClassification, AutoTokenizer, Trainer,
                          TrainingArguments, set_seed)

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
MODELO_PARTIDA = os.path.join(AQUI, "modelos", "beto_further_pretrained")
MODELO_FINAL = os.path.join(AQUI, "modelos", "beto_finetuned_3clases")
DATOS = os.path.join(AQUI, "salidas", "dataset_3clases")
SALIDA = os.path.join(AQUI, "salidas", "entrenamiento")
LABEL_MAP = {"POS": 0, "NEG": 1, "NEU": 2}
CLASES = list(range(len(LABEL_MAP)))
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


def pesos_de_clase(device):
    j = json.load(open(os.path.join(DATOS, "class_weights.json"), encoding="utf-8"))
    return torch.tensor([j["pesos"][l] for l in j["orden_label_id"]], dtype=torch.float).to(device)


def metricas(y, p):
    f1c = f1_score(y, p, average=None, labels=CLASES)
    return {"f1_macro": round(float(f1_score(y, p, average="macro", labels=CLASES)), 4),
            "accuracy": round(float(accuracy_score(y, p)), 4),
            "balanced_accuracy": round(float(balanced_accuracy_score(y, p)), 4),
            **{f"f1_{ID2LABEL[i]}": round(float(f1c[i]), 4) for i in CLASES},
            "n": int(len(y))}


def correr(seed, device, guardar):
    set_seed(seed)
    tr, va, te = (pd.read_csv(os.path.join(DATOS, f"{s}.csv")) for s in ("train", "val", "test"))
    tok = AutoTokenizer.from_pretrained(MODELO_PARTIDA)
    modelo = AutoModelForSequenceClassification.from_pretrained(
        MODELO_PARTIDA, num_labels=len(LABEL_MAP), id2label=ID2LABEL, label2id=LABEL_MAP,
        ignore_mismatched_sizes=True).to(device)
    w = pesos_de_clase(device)

    class WeightedTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            out = model(**inputs)
            loss = nn.CrossEntropyLoss(weight=w)(out.logits, labels)
            return (loss, out) if return_outputs else loss

    def compute_metrics(ev):
        logits, labels = ev
        return {"f1_macro": f1_score(labels, np.argmax(logits, axis=-1), average="macro")}

    tmp = tempfile.mkdtemp(prefix=f"finbeto3_{seed}_", dir=os.environ.get("FASE3_TMP"))
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
    res = {"seed": seed, "minutos": minutos, "historial_val": hist,
           "mejor_epoca": max(hist, key=lambda h: h["val_f1_macro"])["epoca"],
           "test": metricas(y, p),
           "orden_matriz": [ID2LABEL[i] for i in CLASES],
           "matriz_confusion": confusion_matrix(y, p, labels=CLASES).tolist(),
           "textos_de_test_en_train": int(te["texto"].isin(set(tr["texto"])).sum())}
    # las que antes eran MIXTO (ahora NEU): como las clasifica el modelo
    mx = (te["label_original"] == "MIXTO").values
    res["ex_mixto_predichas_como"] = {ID2LABEL[i]: int((p[mx] == i).sum()) for i in CLASES}
    if guardar:
        pd.DataFrame({"texto": te["texto"], "label": te["label"], "label_original": te["label_original"],
                      "pred": [ID2LABEL[i] for i in p], "url": te["url"], "or_idx": te["or_idx"]}
                     ).to_csv(os.path.join(SALIDA, f"predicciones_test_seed{seed}.csv"), index=False, encoding="utf-8")
        trainer.save_model(MODELO_FINAL)
        tok.save_pretrained(MODELO_FINAL)
        res["modelo_guardado_en"] = os.path.relpath(MODELO_FINAL, AQUI)
    shutil.rmtree(tmp, ignore_errors=True)
    del trainer, modelo
    torch.cuda.empty_cache()
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, nargs="+", default=[42, 1, 2])
    ap.add_argument("--guardar-seed", type=int, default=42)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Dispositivo:", device, torch.cuda.get_device_name(0) if device == "cuda" else "")
    os.makedirs(SALIDA, exist_ok=True)
    filas = []
    for seed in a.seeds:
        print(f"\n=== semilla {seed} ===", flush=True)
        r = correr(seed, device, guardar=(seed == a.guardar_seed))
        json.dump(r, open(os.path.join(SALIDA, f"seed{seed}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        f = {"seed": seed, "mejor_epoca": r["mejor_epoca"], "minutos": r["minutos"],
             **{f"test_{k}": v for k, v in r["test"].items()}}
        filas.append(f)
        print(json.dumps(f, ensure_ascii=False), flush=True)
    R = pd.DataFrame(filas)
    R.to_csv(os.path.join(SALIDA, "resumen.csv"), index=False)
    print("\n", R[["test_f1_macro", "test_accuracy", "test_balanced_accuracy"]].agg(["mean", "std"]).round(4).to_string())


if __name__ == "__main__":
    main()
