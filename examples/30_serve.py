"""Ray Serve — deploy a callable service and invoke it through a handle."""

from ray import serve

from _ray_config import init_ray

init_ray()


@serve.deployment(ray_actor_options={"num_cpus": 0.5})
class Greeter:
    def __call__(self, name: str) -> str:
        return f"Hello, {name}!"


handle = serve.run(Greeter.bind(), route_prefix=None)
try:
    response = handle.remote("Ray Serve")
    print(response.result(timeout_s=30))
finally:
    serve.shutdown()
