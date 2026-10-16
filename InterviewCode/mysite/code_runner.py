import docker
from threading import Timer
from contextlib import suppress
from docker.errors import NotFound, DockerException, APIError

client = docker.from_env()

def kill_container(container):
    try:
        container.kill()
    except (NotFound, APIError):
        pass

def run_code(code):
    container = None
    timer = None

    try:
        container = client.containers.run(
            image='python:3.13-slim',
            command=['python', '-c', code],
            network_disabled=True,
            nano_cpus=500_000_000,

            mem_limit="128m",
            pids_limit=64,
            user="nobody",
            read_only=True,
            detach=True,
            stdout=True,
            stderr=True,
        )

        timer = Timer(10, kill_container, [container])
        timer.start()

        count_bytes = 0

        for chunk in container.logs(stream=True, follow=True):
            count_bytes += len(chunk)
            if count_bytes > 10_000:
                kill_container(container)
                yield f"The code terminated because the input limit was exceeded."

                break

            yield chunk.decode('utf-8', errors='replace')

        result = container.wait()
        yield f"\n[Завершено, код выхода: {result['StatusCode']}]\n"

    except Exception as e:
        yield f"Error: {e}"

    finally:
        if timer is not None:
            timer.cancel()

        with suppress(DockerException, AttributeError):
            container.remove(force=True)