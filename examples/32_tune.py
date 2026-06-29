"""Ray Tune — search a parameter space and select the best trial."""

from tempfile import TemporaryDirectory

from ray import tune

from _ray_config import init_ray

init_ray()


def objective(config: dict[str, int]) -> None:
    score = -((config["x"] - 3) ** 2)
    tune.report({"score": score})


with TemporaryDirectory() as storage:
    tuner = tune.Tuner(
        tune.with_resources(objective, {"cpu": 0.5}),
        param_space={"x": tune.grid_search([1, 2, 3, 4])},
        tune_config=tune.TuneConfig(metric="score", mode="max"),
        run_config=tune.RunConfig(name="primer-tune", storage_path=storage, verbose=0),
    )
    results = tuner.fit()
    best = results.get_best_result(metric="score", mode="max")
    print("best config:", best.config)
    print("best score:", best.metrics["score"])
