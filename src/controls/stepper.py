#!/usr/bin/env python3

"""
Created: 12/08/21
by: Sonja Lukas
Tower control with 2 stepper
Motorkit version
"""
import logging
import asyncio
import random

from typing import Literal
from adafruit_motor import stepper as STEPPER
from hardware.stepper_hal import EncoderStepperHAL, StepperHAL
#from asyncio.tasks import current_task

class TowerControl():
    """
        Gamecontroll Stepper

            Attributes:
                angle_max: limit rocking forward stepper1
                angle_min: limit rocking backward stepper1
                interval_max: max. waiting time rotate stepper 2
                interval_min: min. waiting time rotate stepper 2
    """
    max_angle=20
    min_angle=-20
    max_interval=0.05
    min_interval=0.01

    def __init__(self):
        """
            instantiation of the 2 steppers and encoder for rocking stepper

        """
        self.stepper1 = EncoderStepperHAL("myStepper1",1)
        self.stepper2 = StepperHAL("myStepper2",2)
        self.total_score=0
        self.stepper1.encoder.enc_imp=0 
        self.score_goal=int(50) #todo::::: call sdk definition

    async def set_start_position(self):
        """
            set start position after each game round
        """
        steps=self.stepper1.encoder.enc_imp
        await self.stepper1.set_position(steps) #definition open

    async def get_score(self):
        """
            Control depending on the score
            Attribute:
        """
        #in main: function call!
        #scores=score.values(score)
        #total_score=sum(scores)

        # on end:
        # await self.motor_stop() # todo: change in on_end at game_sdk

        #for sim only
        if self.total_score<self.score_goal:
            self.total_score=self.total_score+1
            await asyncio.sleep(2)
        else:
            self.total_score=0
        return self.total_score

    async def game_run(self):
        """
            game starts in game sdk
            mapping attributes to rotate()

            Attributes:
                stepper1: rocking stepper with random start direction
                stepper2: rotate stepper
        """
        stepper1_start_dir=random.randint(0, 1)
        if stepper1_start_dir==0:
            self.stepper1.direction=STEPPER.FORWARD
        else:
            self.stepper1.direction=STEPPER.FORWARD

        asyncio.create_task(self.stepper2.rotate())
        asyncio.create_task(self.stepper1.rotate())

        while True:
            self.stepper1.interval, self.stepper1.direction = await self.stepper1_algo()
            self.stepper2.interval, self.stepper2.direction = await self.stepper2_algo()
            await asyncio.sleep(0.01)

    async def stepper1_algo(self):
        """
            Algorithm of the rocking stepper 1
            The rocking speed is determined via random factor, generated with random.uniform.

            Attributes
                angle_max: limit forward rocking value, definition in class stepperHAL
                angle_min: limit backward rocking value, definition in class stepperHAL
        """
        interval=random.uniform(0.01,0.05)
        logging.debug(f"function call stepper1_algo, random interval: {interval}")

        old_direction:Literal=self.stepper1.direction
        angle = self.stepper1.encoder.angle_calc()
        logging.debug(f"stepper1_algo get angle {angle}")
        if angle >= self.max_angle:
            if old_direction==STEPPER.FORWARD:
                new_dire=STEPPER.BACKWARD
                logging.info(f"direction changes: {STEPPER.BACKWARD}, Trigger: max_angle")
                return interval, new_dire
            else:
                logging.info(f"ERROR Trigger: angle_max")

        elif angle <= self.min_angle:
            if old_direction==STEPPER.BACKWARD:
                new_dire=STEPPER.FORWARD
                logging.info(f"direction changes: {STEPPER.FORWARD}, Trigger: min_angle")
                return interval, new_dire
            else:
                logging.info(f"ERROR Trigger: angle_min")
        else:
            return interval, old_direction

    async def score_map(self, x, in_min, in_max, out_min, out_max):
        """
        maps the percentage range -100 to -1 or 1 to 100  to interval range 0.01 to 0.05

        """
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

    async def stepper2_algo(self):
        """
            Algorithm of the rotate stepper 2

            Attributes:
                The rotation interval depends on the total score of the players.
                A change of direction is possible, but currently not included in the game definition.
        """
        direction:Literal=self.stepper2.direction
        current_score=await self.get_score()

        interval=await self.score_map(current_score, 0, self.score_goal, self.max_interval, self.min_interval)
        logging.info(f"function call stepper2_algo, score: {current_score} mapping to interval {interval}")
        return interval, direction

    async def score_map(self, x, in_min, in_max, out_min, out_max):
        """
        maps the percentage range -100 to -1 or 1 to 100  to interval range 0.01 to 0.05

        """
        return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    async def on_exit(self):
        """
            threading stop, motor_release via atexit register
        """
        await self.set_start_position()
        self.close()    #todo:::::::::::: check hal.close
        #stepper1.close()
        #stepper2.close()

Tower1=TowerControl()

async def main():
    await asyncio.gather(Tower1.game_run())

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main())