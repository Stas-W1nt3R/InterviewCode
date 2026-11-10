import logging
from contextlib import suppress
from threading import Timer

import docker
from docker.errors import APIError, DockerException, NotFound

logger = logging.getLogger(__name__)

client = docker.from_env()
room_dict = {}

def kill_container(container, reason=None):
    if reason == 'timer':
        logger.warning('The %s was terminated because it exceeded its runtime', container)
    with suppress(NotFound, APIError):
        container.kill()

def run_code(code, uuid):
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

        logger.info("Container in room %s created", uuid)

        room_dict[uuid] = container

        timer = Timer(10, kill_container, [container], kwargs={'reason': 'timer'})
        timer.start()

        count_bytes = 0

        for chunk in container.logs(stream=True, follow=True):
            count_bytes += len(chunk)
            if count_bytes > 10_000:
                kill_container(container)
                logger.warning("Container in room %s was terminated because the data output limit was exceeded", uuid)
                yield "The code terminated because the input limit was exceeded."

                break

            yield chunk.decode('utf-8', errors='replace')

        result = container.wait()
        logger.info("Container in room %s completed with code %s", uuid, result['StatusCode'])
        yield f"\n[Завершено, код выхода: {result['StatusCode']}]\n"

    except Exception as e:
        logger.exсeption("Container run fail in room %s: %r", uuid, e)
        yield f"Error: {e}"

    finally:
        if timer is not None:
            timer.cancel()

        with suppress(DockerException, AttributeError):
            container.remove(force=True)
            logger.info("Container in room %s removed", uuid)

        room_dict.pop(uuid, None)

def is_running(uuid):
    return uuid in room_dict

def stop_code(uuid):
    try:
        kill_container(room_dict[uuid])
        logger.info("Container in room %s stopped by user", uuid)
    except KeyError:
        return False

    return True
