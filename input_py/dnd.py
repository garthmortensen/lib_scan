# -*- coding: utf-8 -*-
"""
Created on Fri Jul 29 19:31:56 2022

@author: garth

make classes and sqlalchemy fun with dnd
maybe add some unit tests and logging
"""
# %%

import random  # for dice rolling
import os

# change working directory to this script location
dir_py = os.path.dirname(__file__)
os.chdir(dir_py)

import db


# %%

engine, metadata = db.setup_db()
engine, metadata, rolls_t, chars_t = db.setup_tables(engine, metadata)
# db.update_rows(engine, rolls_t)
# db.select_rows(engine, rolls_t)
# row_count = db.count_rows(engine, rolls_t)
# db.delete_rows_all(engine, rolls_t)

# %%


class Die(object):
    def __init__(self, sides=6):
        self.sides = sides

    def roll_die(self, reason='Not provided'):
        roll_value = random.randint(1, self.sides)

        data = {
                'reason': reason,
                'sides': self.sides,
                'roll_value': roll_value
                }

        db.insert_rows(engine, rolls_t, data)

        return roll_value


class CupOfDice(object):
    def __init__(self):
        self.dice = []

    def add_dice(self, *add_dice):
        self.dice += add_dice

    def remove_dice(self, *del_dice):
        self.dice -= del_dice

    def roll_dice(self, reason='Not provided'):
        roll_values = []
        for die in self.dice:
            roll_value = die.roll_die(reason)
            roll_values.append(roll_value)
        return roll_values

# %%

# check dice functionality
one_d_four = Die(4)
roll_value = one_d_four.roll_die('saving throw')

cup = CupOfDice()
cup.add_dice(Die(4), Die(6))
cup.roll_dice('saving throw')
row_count = db.count_rows(engine, rolls_t)
db.select_rows(engine, rolls_t)

# %%

class Character(object):
    """Create character. Write attributes to db tables. Update tables on set"""
    def __init__(self,
                 char_name="Brutus",
                 char_race="human",
                 char_class="fighter",
                 char_alignment="chaotic good"):

        self.char_name = char_name
        self.char_race = char_race
        self.char_class = char_class
        self.char_alignment = char_alignment
        
        self.ability_rolls = []
        self.strength = 0
        self.dexterity = 0
        self.constitution = 0
        self.intelligence = 0
        self.wisdom = 0
        self.charisma = 0
        
        # insert data into chars_t
        data = {
                'char_name':        self.char_name,
                'char_race':        self.char_race,
                'char_class':       self.char_class,
                'char_alignment':   self.char_alignment,
                'strength':         self.strength,
                'dexterity':        self.dexterity,
                'constitution':     self.constitution,
                'intelligence':     self.intelligence,
                'wisdom':           self.wisdom,
                'charisma':         self.charisma,
                }

        db.insert_rows(engine, chars_t, data)

    def roll_ability_score(self):
        """roll 4d6 and discard the lowest"""
        cup = CupOfDice()
        cup.add_dice(Die(6), Die(6), Die(6), Die(6))
        roll_values = cup.roll_dice("ability score roll")

        # discard lowest roll, per dnd5e
        roll_values.remove(min(roll_values))
        return sum(roll_values)

    def roll_ability_scores(self):
        ability_rolls = []
        for each in range(6):
            roll_values = self.roll_ability_score()
            ability_rolls.append(roll_values)
        self.ability_rolls = ability_rolls

    def assign_scores(self):
        # could dict
        self.strength = self.ability_rolls[0]
        self.dexterity = self.ability_rolls[1]
        self.constitution = self.ability_rolls[2]
        self.intelligence = self.ability_rolls[3]
        self.wisdom = self.ability_rolls[4]
        self.charisma = self.ability_rolls[5]
        del self.ability_rolls
        
        # @TODO: update chars_t
        # db.update_rows(engine, chars_t)

        

    def get_char_sheet(self):
        # could dict
        return \
        f"""{self.char_name}:
        strength: {self.strength}
        dexterity: {self.dexterity}
        constitution: {self.constitution}
        intelligence: {self.intelligence}
        wisdom: {self.wisdom}
        charisma: {self.charisma}
        """
        
# check Character functionality
gimli = Character("gimli", "dwarf", "cleric", "lawful good")
gimli.roll_ability_scores()
gimli.assign_scores()
char_sheet = gimli.get_char_sheet()

# %%

# print(vars(gimli))
db.select_rows(engine, chars_t)

# %%

db.select_rows(engine, rolls_t)

# %%

    # python get/set
    # class Foo(object):
    #     def __init__(self, x):
    #         self.x = x
    
    # f = Foo(10)
    # print(f.x)  # 10
    # f.x = 20
    # print(f.x)  # 20

    # get/set with protections
    # @property
    # def char_race(self):
    #     return self._char_race

    # @char_race.setter
    # def char_race(self, new_char_race):
    #     if type(new_char_race) == str \
    #             and new_char_race.lower() in ["human", "dwarf", "elf", "halfling"]:
    #         self.char_race = new_char_race
    #     else:
    #         raise Exception("Choose from human, dwarf, elf, halfling")
