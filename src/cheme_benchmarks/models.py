"""Fixed baseline search spaces and preprocessing learned on training rows only."""
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor, HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

GRIDS = {
    "mean": [{"strategy": "mean"}],
    "ridge": [{"alpha": a} for a in (0.1, 1.0, 10.0)],
    "random_forest": [{"n_estimators": 100, "max_depth": d, "min_samples_leaf": 2} for d in (8, None)],
    "hist_gradient_boosting": [{"max_iter": 100, "max_leaf_nodes": leaves, "learning_rate": 0.1, "early_stopping": False} for leaves in (15, 31)],
}


def preprocessing(features):
    numeric = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)), ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="__missing__")),
                            ("encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    return ColumnTransformer([("numeric", numeric, features["numeric"]), ("categorical", categorical, features["categorical"])], remainder="drop")


def model_pipeline(name, params, features, seed):
    if name == "mean":
        estimator = DummyRegressor(**params)
    elif name == "ridge":
        estimator = Ridge(**params)
    elif name == "random_forest":
        estimator = RandomForestRegressor(**params, random_state=seed, n_jobs=1)
    elif name == "hist_gradient_boosting":
        estimator = HistGradientBoostingRegressor(**params, random_state=seed)
    else:
        raise ValueError(f"Unknown baseline: {name}")
    return Pipeline([("preprocess", preprocessing(features)), ("model", estimator)])
