from json.decoder import JSONDecodeError
from typing import Any
from paho.mqtt.client import MQTTMessage
from asyncio_mqtt import Client
import enum
import logging
import json


class GameState(enum.Enum):
    """
        Different states of the game
    """

    IDLE = "idle"
    START = "start"
    RUN = "run"
    END = "end"


class GameIO:
    """
    Core of the game-sdk. Used to communicate with other controllers and the gamecontrol.
    """

    client: Client
    """ MQTT Client """

    def __init__(self, mqtt_conf: dict):
        """
        Arguments:
            mqtt_conf: Information needed to connect controller to the mqtt broker
        """

        self._ip = mqtt_conf['broker_ip']
        self._port = mqtt_conf['broker_port'] if 'broker_port' in mqtt_conf else 1883
        self._uname = mqtt_conf['username'] if 'username' in mqtt_conf else None
        self._passwd = mqtt_conf['password'] if 'password' in mqtt_conf else None

        self.client = Client(self._ip, self._port,
                             username=self._uname, password=self._passwd)

    async def connect(self):
        """
            Connect to MQTT client
        """
        await self.client.connect()

    async def subscribe(self, topics: list):
        """
            Subscribe to the different MQTT topics published by the gamecontrol

            Arguments:
                topics: List of topics to subscribe to. Each topic is a tuple consisting of the actual topic and QOS e.g. ("some/topic", 0)
        """

        async with self.client.unfiltered_messages() as messages:
            await self.client.subscribe(topics)
            async for msg in messages:
                msg: MQTTMessage = msg

                try:
                    data = json.loads(msg.payload)

                    yield (msg.topic, data)
                except JSONDecodeError:
                    logging.warning("Got MQTT message with wrong format")

    async def subscribe_to_status(self):
        """
            Subscribe to the gamestatus published by the gamecontrol
        """

        topics = [("status/game", 0)]

        async for msg in self.subscribe(topics):
            data = msg[1]
            mode = data['mode'] if 'mode' in data else 'idle'

            game_state = GameState.IDLE
            if mode == 'start':
                game_state = GameState.START
            elif mode == 'run':
                game_state = GameState.RUN
            elif mode == 'end':
                game_state = GameState.END
            yield game_state

    async def publish(self, topic: str, payload: dict):
        """
            Publish any message to any desired topic
        """

        try:
            logging.debug("Publish to: %s with %s", topic, payload)
            await self.client.publish(topic, json.dumps(payload))
        except TypeError:
            logging.error("MQTT Payload is not JSON serializable")

    async def ready(self, seat: int):
        """
            Publish ready state

            Arguments:
                seat: Controller seat
        """

        payload = dict(seat=seat, ready=True)
        await self.publish('status/ready', payload)

    async def score(self, score: int, seat: int):
        """
            Publish score

            Arguments:
                score: Score
                seat: Controller seat
        """
        payload = dict(seat=seat, score=score)
        await self.publish('score', payload)

    async def set_game_state(self, state: GameState):
        """
            Publish new `game_state`

            Arguments:
                state: State to publish
        """

        payload = dict(mode=state.value)
        await self.publish("status/game", payload)
