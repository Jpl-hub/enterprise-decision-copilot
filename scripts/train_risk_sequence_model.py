from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import settings


FEATURES = [
    "revenue_million",
    "net_profit_million",
    "gross_margin_pct",
    "net_margin_pct",
    "rd_ratio_pct",
    "debt_ratio_pct",
    "current_ratio",
    "cash_to_short_debt",
    "inventory_turnover",
    "receivable_turnover",
    "operating_cashflow_million",
    "roe_pct",
]
SEQUENCE_LENGTH = 3


def load_financial_panel() -> pd.DataFrame:
    path = settings.processed_dir / "financial_features.csv"
    if not path.exists():
        raise FileNotFoundError(f"未找到文件：{path}")
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError("financial_features.csv 为空，无法训练。")
    frame["report_year"] = frame["report_year"].astype(int)
    frame = frame.sort_values(["company_code", "report_year"]).reset_index(drop=True)
    return frame


def build_risk_label(frame: pd.DataFrame) -> pd.DataFrame:
    penalties = (
        (frame["debt_ratio_pct"] > 60).astype(int)
        + (frame["cash_to_short_debt"] < 1).astype(int)
        + (frame["operating_cashflow_million"] < 0).astype(int)
        + (frame["current_ratio"] < 1.2).astype(int)
    )
    frame = frame.copy()
    frame["risk_label"] = (penalties >= 2).astype(int)
    return frame


def make_sequences(frame: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    sequences = []
    labels = []
    for _, group in frame.groupby("company_code"):
        if len(group) <= SEQUENCE_LENGTH:
            continue
        values = group[FEATURES].astype(float).to_numpy()
        targets = group["risk_label"].astype(int).to_numpy()
        for start in range(len(group) - SEQUENCE_LENGTH):
            end = start + SEQUENCE_LENGTH
            sequences.append(values[start:end])
            labels.append(targets[end])
    if not sequences:
        raise ValueError("可训练的时序样本不足，至少需要多家公司多年真实数据。")
    return np.array(sequences, dtype=np.float32), np.array(labels, dtype=np.float32)


def build_model(input_shape: tuple[int, int]) -> tf.keras.Model:
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=input_shape),
            tf.keras.layers.LSTM(64, return_sequences=True),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="binary_crossentropy",
        metrics=["accuracy", tf.keras.metrics.AUC(name="auc")],
    )
    return model


def main() -> None:
    frame = build_risk_label(load_financial_panel())
    frame[FEATURES] = frame[FEATURES].fillna(0)
    scaler = StandardScaler()
    frame[FEATURES] = scaler.fit_transform(frame[FEATURES])

    x, y = make_sequences(frame)
    x_train, x_val, y_train, y_val = train_test_split(
        x, y, test_size=0.3, random_state=42, stratify=y if len(set(y)) > 1 else None
    )

    model = build_model((x.shape[1], x.shape[2]))
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_auc", patience=8, mode="max", restore_best_weights=True)
    ]
    history = model.fit(
        x_train,
        y_train,
        validation_data=(x_val, y_val),
        epochs=80,
        batch_size=16,
        callbacks=callbacks,
        verbose=2,
    )

    output_dir = settings.cache_dir / "models"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "risk_lstm.keras"
    model.save(model_path)
    print("模型已保存：", model_path)
    print("最佳验证 AUC：", max(history.history.get("val_auc", [0])))


if __name__ == "__main__":
    main()
