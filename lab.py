"""6.009 Fall 2019 Lab 9 -- 6.009 Zoo"""

from math import acos
# NO OTHER IMPORTS ALLOWED!

class Constants:
    """
    A collection of game-specific constants.

    You can experiment with tweaking these constants, but
    remember to revert the changes when running the test suite!
    """
    # width and height of keepers
    KEEPER_WIDTH = 30
    KEEPER_HEIGHT = 30

    # width and height of animals
    ANIMAL_WIDTH = 30
    ANIMAL_HEIGHT = 30

    # width and height of food
    FOOD_WIDTH = 10
    FOOD_HEIGHT = 10

    # width and height of rocks
    ROCK_WIDTH = 50
    ROCK_HEIGHT = 50

    # thickness of the path
    PATH_THICKNESS = 30

    TEXTURES = {
        'rock': '1f5ff',
        'animal': '1f418',
        'SpeedyZookeeper': '1f472',
        'ThriftyZookeeper': '1f46e',
        'CheeryZookeeper': '1f477',
        'food': '1f34e'
    }

    FORMATION_INFO = {'SpeedyZookeeper':
                       {'price': 9,
                        'interval': 55,
                        'throw_speed_mag': 20},
                      'ThriftyZookeeper':
                       {'price': 7,
                        'interval': 45,
                        'throw_speed_mag': 7},
                      'CheeryZookeeper':
                       {'price': 10,
                        'interval': 35,
                        'throw_speed_mag': 2}}

        
class NotEnoughMoneyError(Exception):
    """A custom exception to be used when insufficient funds are available
    to hire new zookeepers. You may leave this class as is."""
    pass


################################################################################
################################################################################

class Game:
    def __init__(self, game_info):
        """Initializes the game.

        `game_info` is a dictionary formatted in the following manner:
          { 'width': The width of the game grid, in an integer (i.e. number of pixels).
            'height': The height of the game grid, in an integer (i.e. number of pixels).
            'rocks': The set of tuple rock coordinates.
            'path_corners': An ordered list of coordinate tuples. The first
                            coordinate is the starting point of the path, the
                            last point is the end point (both of which lie on
                            the edges of the gameboard), and the other points
                            are corner ("turning") points on the path.
            'money': The money balance with which the player begins.
            'spawn_interval': The interval (in timesteps) for spawning animals
                              to the game.
            'animal_speed': The magnitude of the speed at which the animals move
                            along the path, in units of grid distance traversed
                            per timestep.
            'num_allowed_unfed': The number of animals allowed to finish the
                                 path unfed before the player loses.
          }
        """
        self.width = game_info['width']
        self.height = game_info['height']
        self.rocks =game_info['rocks']
        self.corners =game_info['path_corners']
        self.money = game_info['money']
        self.interval = game_info['spawn_interval']
        self.speed = game_info['animal_speed']
        self.unfed = game_info['num_allowed_unfed']
        self.zookeeper_list = []
        self.animal_set = set()
        self.food_set = set()
        self.current_keeper_type = None
        self.current_keeper_position = None
        self.status = 'ongoing'
        self.time = 0
        self.start_time = 0
    
    # record the nunmber of animals still can be unfed to exit the board before the game status is `'defeat'`.
    def num_allow(self):
        return self.unfed
    
    # the getter of the gamining status
    def get_status(self):
        return self.status
    
    # the getter of the coordinates of each corner of a path
    def get_corners(self):
        return self.corners
    
    # the getter of the remaining money of player
    def money_remaining(self):
        return self.money
    
    # the getter of the food_set
    def get_food_set(self):
        return self.food_set.copy()
    
    # the getter of the animal_set
    def get_animal_set(self):
        return self.animal_set.copy()
    
    # the getter of the zookeeper_list
    def get_zookeeper_list(self):
        return self.zookeeper_list.copy()
    
    def check_collision(self, new_position, graph_dir):
        """
        check if a keeper at a desired location will collide with other formations in the board
        """
        
        # if the keeper overlaps with existing rocks or keepers, determine as collision
        for block in self.rocks:
            if (abs(new_position[0] - block[0]) < Constants.KEEPER_WIDTH / 2 + Constants.ROCK_WIDTH / 2 and \
            abs(new_position[1] - block[1]) < Constants.KEEPER_HEIGHT / 2 + Constants.ROCK_HEIGHT / 2):
                return True
        
        for block in self.zookeeper_list:
            if abs(new_position[0] - block.position[0]) <  Constants.KEEPER_WIDTH and \
            abs(new_position[1] - block.position[1]) < Constants.KEEPER_HEIGHT:
                return True
        
        # if the keeper overlaps with path, determine as collision
        for pair in graph_dir:
            if pair[0][0] == pair[1][0]:
                if abs(new_position[0] - pair[0][0]) < Constants.KEEPER_WIDTH / 2 + Constants.PATH_THICKNESS / 2 and \
                max(min(pair[0][1], pair[1][1]) - Constants.PATH_THICKNESS / 2, 0) < new_position[1] < min(max(pair[0][1], pair[1][1]) + Constants.PATH_THICKNESS / 2, self.height):
                    return True
                
            if pair[0][1] == pair[1][1]:
                if abs(new_position[1] - pair[0][1]) < Constants.KEEPER_WIDTH / 2 + Constants.PATH_THICKNESS / 2 and \
                max(min(pair[0][0], pair[1][0]) - Constants.PATH_THICKNESS / 2, 0) < new_position[0] < min(max(pair[0][0], pair[1][0]) + Constants.PATH_THICKNESS / 2, self.width):
                    return True
        
        # else, determine as no collision
        return False
    
    def get_direction(self):
        """
        get the starting and ending points of each path segment in a given path
        """
        graph_dir = []
        for i in range(len(self.corners) - 1):
            graph_dir.append((self.corners[i], self.corners[i+1]))
        
        return graph_dir
        
    def get_cord(self, specific_position):
        """
        get cordinates of four corners of a rectangular animal and storing them into a list in the clock-wise order
        """
        left_top = (specific_position[0] - Constants.ANIMAL_WIDTH/2, specific_position[1] - Constants.ANIMAL_HEIGHT/2)
        left_bot = (specific_position[0] - Constants.ANIMAL_WIDTH/2, specific_position[1] + Constants.ANIMAL_HEIGHT/2)
        right_top = (specific_position[0] + Constants.ANIMAL_WIDTH/2, specific_position[1] - Constants.ANIMAL_HEIGHT/2)
        right_bot = (specific_position[0] + Constants.ANIMAL_WIDTH/2, specific_position[1] + Constants.ANIMAL_HEIGHT/2)
        return [left_top, right_top, right_bot, left_bot]
    
    def deter_angle(self, v1, v2):
        """
        determine the angle between two vectors
        """
        expression = (v1[0]*v2[0] + v1[1]*v2[1])/((v1[0]**2+v1[1]**2)**0.5 * (v2[0]**2+v2[1]**2)**0.5)
        return acos(expression)
    
    def deter_intersect(self, keeper, a):
        """
        determine if the line of sight of a zookeeper intersects with a rectangular animal
        """
        cord_list = self.get_cord(a.position)
        cord_list = cord_list + [cord_list[0]]
        for i in range(len(cord_list) - 1):
            vec1 = (cord_list[i][0] - keeper.position[0], cord_list[i][1] - keeper.position[1])
            vec2 = (cord_list[i+1][0] - keeper.position[0], cord_list[i+1][1] - keeper.position[1])
            vec_ray = keeper.aiming_vector
            
            if abs(self.deter_angle(vec1, vec2) - (self.deter_angle(vec1, vec_ray) + self.deter_angle(vec_ray, vec2))) <= 0.001:
                return True
        return False
    
    def render(self):
        """Renders the game in a form that can be parsed by the UI.

        Returns a dictionary of the following form:
          { 'formations': A list of dictionaries in any order, each one
                          representing a formation. The list should contain 
                          the formations of all animals, zookeepers, rocks, 
                          and food. Each dictionary has the key/value pairs:
                             'loc': (x, y), 
                             'texture': texture, 
                             'size': (width, height)
                          where `(x, y)` is the center coordinate of the 
                          formation, `texture` is its texture, and `width` 
                          and `height` are its dimensions. Zookeeper
                          formations have an additional key, 'aim_dir',
                          which is None if the keeper has not been aimed, or a 
                          tuple `(aim_x, aim_y)` representing a unit vector 
                          pointing in the aimed direction.
            'money': The amount of money the player has available.
            'status': The current state of the game which can be 'ongoing' or 'defeat'.
            'num_allowed_remaining': The number of animals which are still
                                     allowed to exit the board before the game
                                     status is `'defeat'`.
          }
        """
        result = {}

        formation_list = []
        
        # for each kind of formations, exacting them from the corresponding set and storing its information in a dictionary
        
        # Food
        for food in self.food_set:
            f_food = {'loc': food.position, 'texture': Constants.TEXTURES['food'], \
                                        'size': (Constants.FOOD_WIDTH, Constants.FOOD_HEIGHT)}
            if f_food not in formation_list:
                formation_list.append(f_food)
        # Animal
        for animal in self.animal_set:
            f_animal = {'loc': animal.position, 'texture': Constants.TEXTURES['animal'], \
                                        'size': (Constants.ANIMAL_WIDTH, Constants.ANIMAL_HEIGHT)}
            if f_animal not in formation_list:
                formation_list.append(f_animal)
        # Zookeeper
        for keeper in self.zookeeper_list:
            f_keeper = {'loc': keeper.position, 'texture': Constants.TEXTURES[keeper.name], \
                                        'size': (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT), 'aim_dir': keeper.aiming_vector}
            if f_keeper not in formation_list:   
                formation_list.append(f_keeper)
        # Rock
        for rock in self.rocks:
            formation_list.append({'loc': rock, 'texture': Constants.TEXTURES['rock'], \
                                        'size': (Constants.ROCK_WIDTH, Constants.ROCK_HEIGHT)})
              
        result['formations'] = formation_list
        
        # store other information into the dictionary
        result['money'] = self.money_remaining()
        result['status'] = self.get_status()
        result['num_allowed_remaining'] = self.unfed
        return result
        
    def keeper_placement(self, mouse, graph_dir):
        """
        place a zookeeper at a desired location and set his aiming vector. mouse is the input information collected from UI,
        while graph_dir is a list storing the starting and ending point of each segment in the path
        """
        # if the user choosing the type of zookeeper, store this type in the current_keeper_condition 
        if type(mouse) == str:
            self.current_keeper_type = mouse
        # if the input is a tuple and the user has chosen the type of zookeeper, check if the position of the chosen
        # zookeeper has been set
        if type(mouse) == tuple and self.current_keeper_type != None:
            # if the chosen zookeeper has not been placed, check if the remaining money is enough to buy the chosen keeper
            if self.current_keeper_position == None:
                # if the money is less than the price of the chosen keeper, raise error
                if self.money_remaining() < Constants.FORMATION_INFO[self.current_keeper_type]['price']:
                    raise NotEnoughMoneyError
                # if the money is enough, check if the input location is valid
                else:
                    # if the input location will not cause the collision of the chosen keeper with other formations, place 
                    # the chosen keeper to the input location and add him into the zookeeper_list and update the remaining money
                    if not self.check_collision(mouse, graph_dir):
                        self.current_keeper_position = mouse
                        
                        # build up the corresponding instance of class according to the chosen type of zookeeper
                        if self.current_keeper_type == 'SpeedyZookeeper':
                            keeper = SpeedyZookeeper(mouse, self.time + 1, \
                                                     Constants.FORMATION_INFO['SpeedyZookeeper']['price'], \
                                                     Constants.FORMATION_INFO['SpeedyZookeeper']['interval'], \
                                                     Constants.FORMATION_INFO['SpeedyZookeeper']['throw_speed_mag'])
                                                     
                        if self.current_keeper_type == 'ThriftyZookeeper':
                            keeper = ThriftyZookeeper(mouse, self.time + 1, \
                                                     Constants.FORMATION_INFO['ThriftyZookeeper']['price'], \
                                                     Constants.FORMATION_INFO['ThriftyZookeeper']['interval'], \
                                                     Constants.FORMATION_INFO['ThriftyZookeeper']['throw_speed_mag'])
                            
                        if self.current_keeper_type == 'CheeryZookeeper':
                            keeper = CheeryZookeeper(mouse, self.time + 1, \
                                                     Constants.FORMATION_INFO['CheeryZookeeper']['price'], \
                                                     Constants.FORMATION_INFO['CheeryZookeeper']['interval'], \
                                                     Constants.FORMATION_INFO['CheeryZookeeper']['throw_speed_mag'])
                            
                        self.zookeeper_list.append(keeper)
                        self.money -= Constants.FORMATION_INFO[self.current_keeper_type]['price']
            # if the chosen keeper has been placed to the desired location, setting the aiming vector according to the
            # input tuple if the tuple is different from the the keeper coordinates 
            else:
                if mouse != self.current_keeper_position:
                    self.zookeeper_list[-1].set_aiming_dir(mouse)
                    # clean what is store in current_keeper_type and current_keeper_position
                    self.current_keeper_type = self.current_keeper_position = None
                    
    
    def animal_spawning(self):
        """
        spawning a new animal at the starting point of the path at an appropriate time
        """
        if (self.time - self.start_time) % self.interval == 0:
            a = Animal(self.corners[0], self.time, self.speed)
            self.animal_set.add(a)
    
    def removing(self, a):
        """
        if the location of a formation is out of the board, return True; else, return False
        """
        if a.position[1] < 0 or a.position[1] > self.height or a.position[0] < 0 or a.position[0] > self.width:
            #if a.feed_status == False:
            return True
        else:
            return False
    
    def animal_moving(self, a, graph_dir):
        """
        Determine the position of an animal in next timestep given its position at this timestep.
        graph_dir is a list storing the starting and ending point of a path segment
        """
        # initialize the total length of an animal travelling in this timestep
        total_length = 0
        
        # check each path segment to determine the moving direction of the animal
        for i in range(len(graph_dir)):
            pair = graph_dir[i]
            # determine the vector of moving in the current path segment 
            vec_segment = (pair[1][0] - pair[0][0], pair[1][1] - pair[0][1])
            # if the vector is vertical and the animal is on this path segment, determine if the remaining speed is large enough
            # to allow the animal pass this segment
            if vec_segment[0] == 0 and a.position[0] == pair[0][0] and min(pair[0][1], pair[1][1]) <= a.position[1] <= max(pair[0][1], pair[1][1]): 
                # if yes, check if the current segment is the last segment of the path; if yes, the next position of the animal
                # should be out of board; if no, move the animal to the ending point of the current segment and check the next segment
                if (a.speed - total_length) > abs(pair[1][1] - a.position[1]):
                    if pair == graph_dir[-1]:
                        a.position = (a.position[0], a.position[1] + round(vec_segment[1] / abs(vec_segment[1]) * (a.speed - total_length)))
                        break
                    else:
                        total_length += abs(pair[1][1] - a.position[1])
                        a.position = (a.position[0], pair[1][1])
                        continue
                    
                # if the remaining speed is not large enough to allow the animal finish the current segment, then just updating its location
                else:
                    a.position = (a.position[0], a.position[1] + round(vec_segment[1] / abs(vec_segment[1]) * (a.speed - total_length)))
                    break
            
            # if the vector is horizonal, do the similar things as the case shown above
            if vec_segment[1] == 0 and a.position[1] == pair[0][1] and min(pair[0][0], pair[1][0]) <= a.position[0] <= max(pair[0][0], pair[1][0]):
                if (a.speed - total_length) > abs(pair[1][0] - a.position[0]):
                    if pair == graph_dir[-1]:
                        a.position = (a.position[0] + round(vec_segment[0] / abs(vec_segment[0]) * (a.speed - total_length)), a.position[1])
                        break
                    else:
                        total_length += abs(pair[1][0] - a.position[0])
                        a.position = (pair[1][0], a.position[1])
                        continue
                else:
                    a.position = (a.position[0] + round(vec_segment[0] / abs(vec_segment[0]) * (a.speed - total_length)), a.position[1])
                    break
                    
    def food_throwing(self):
        """
        for each keeper storing in the zookeeper_list, determining if he should throw a new food in this timestep. 
        """
        for keeper in self.zookeeper_list:
            # if the keeper has an aiming vector, determine if the current timestep is appropriate to throw the food
            # according to the throw_interval of the keeper
            if keeper.aiming_vector != None:
                if (self.time - keeper.time_setup) % keeper.time_interval == 0:
                    # if the time is determined as appropriate, determine if the sight line of the keeper intersects 
                    # with any animal; if yes, throw the new food from the center of keeper
                    for animal in self.get_animal_set():
                        if self.deter_intersect(keeper, animal):
                            food_throw = Food(keeper.position, self.time, keeper.aiming_vector, keeper.food_speed)
                            self.food_set.add(food_throw)
                            break
                        
    def food_moving(self):
        """
        for each food storing in the food_set, calculating its position in the next timestep according to its direction 
        and speed of throwing
        """
        for food in self.get_food_set():
            next_position = (food.position[0] + food.direction[0] * food.speed, food.position[1] + food.direction[1] * food.speed)
            food.position = next_position
    
    def feeding_animal(self):
        """
        for each food storing in the food_set, check if it overlaps with any animal; remove all of animals overlapping with it
        and remove the food if it is used to feed at least one animal
        """
        for food in self.get_food_set():
            for animal in self.get_animal_set():
                if (abs(animal.position[0] - food.position[0]) < Constants.ANIMAL_WIDTH / 2 + Constants.FOOD_WIDTH / 2 and \
                    abs(animal.position[1] - food.position[1]) < Constants.ANIMAL_HEIGHT / 2 + Constants.FOOD_HEIGHT / 2):
                        self.animal_set.remove(animal)
                        self.money += 1
                        food.used = True
            if food.used:
                self.food_set.remove(food)
                
    def timestep(self, mouse=None):
        """Simulates the evolution of the game by one timestep.

        In this order:
            (0. Do not take any action if the player is already defeated.)
            1. Compute any changes in formation locations, then remove any
                off-board formations.
            2. Handle any food-animal collisions, and remove the fed animals
                and eaten food.
            3. Throw new food if possible.
            4. Spawn a new animal from the path's start if needed.
            5. Handle mouse input, which is the integer coordinate of a player's
               click, the string label of a particular zookeeper type, or `None`.
            6. Redeem one unit money per animal fed this timestep.
            7. Check for the losing condition to update the game status if needed.
        """
        # if the game status is ongoing 
        if self.status == 'ongoing':
            graph_dir = self.get_direction()
           # 1. compute change in formations locations and remove any off-board formations:
            for animal in self.get_animal_set():
                self.animal_moving(animal, graph_dir)
                if self.removing(animal):
                    self.unfed -= 1
                    self.animal_set.remove(animal)
                    
            for food in self.get_food_set():
                self.food_moving()
                if self.removing(food):
                    self.food_set.remove(food)
            
            # 2. handle the collision between food and animal and redeem the money for animal feeding:
            self.feeding_animal()
            
            # 3. throw new food:
            self.food_throwing()
            
            # 4. spawn a new animal if needed:
            self.animal_spawning()
            
            # 5. handle a mouse input for keeper placement:
            if mouse != None:
                self.keeper_placement(mouse, graph_dir)
            
            # 6. check the losing condition of the game
            if self.unfed >= 0:
                self.status = 'ongoing'
            else:
                self.status = 'defeat'
                
        # update the timestep
        self.time += 1
            


################################################################################
################################################################################
# TODO: Add a Formation class and at least two additional classes here.
            
class Formation():
    '''
    A formation can represent any object in the game with a position, size, and texture. 
    Textures determine how the formation looks when rendered in the UI. They are string codes 
    like defined in the Constants.TEXTURES dictionary of lab.py
    
    Some formations might be moving formations. Those may have both an x-directional and a y-directional
    velocity, in units of distance traversed per timestep.

    Throughout the game, collision detection will be based on the overlap between these rectangular formations. 
    One formation intersects (i.e. collides) with another if any part of it overlaps with the other. Shared edges 
    and corners do not count as intersections.

    Note that formations may leave the board during the game. We say a formation has left the board if its center 
    is no longer on the board. Coordinates on edges and corners of the board (such as (0,0)) are still on the board.
    '''
    def __init__(self, name, size, position, time):
        self.name = name
        self.width = size[0]
        self.height = size[1]
        self.position = position
        self.time_setup = time
    
    def get_position(self):
        return self.position
    
    def get_dimension(self):
        return (self.width, self.height)
    
    def get_formation(self):
        return self.name
    
# The formation of a zookeeper
class Zookeepers(Formation):
    def __init__(self, name, size, position, time):
        Formation.__init__(self, name, size, position, time)
        self.moving = False
        self.aiming_vector = None
        
    def set_aiming_dir(self, mouse):
        vector = (mouse[0] - self.position[0], mouse[1] - self.position[1])
        magnitude = ((mouse[0] - self.position[0])**2 + (mouse[1] - self.position[1])**2)**0.5
        self.aiming_vector = (vector[0]/magnitude, vector[1]/magnitude)       
          
# Three subclasses of zookeeper 
class SpeedyZookeeper(Zookeepers):
    def __init__(self, position, time, price, time_interval, food_speed, name = 'SpeedyZookeeper', size = (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT)):
        Zookeepers.__init__(self, name, size, position, time)
        self.texture = Constants.TEXTURES['SpeedyZookeeper']
        self.price = price
        self.time_interval = time_interval
        self.food_speed = food_speed
    
    def get_texture(self):
        return self.texture
    
class ThriftyZookeeper(Zookeepers):
    def __init__(self, position, time, price, time_interval, food_speed, name = 'ThriftyZookeeper', size = (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT)):
        Zookeepers.__init__(self, name, size, position, time)
        self.texture = Constants.TEXTURES['ThriftyZookeeper']
        self.price = price
        self.time_interval = time_interval
        self.food_speed = food_speed
    
    def get_texture(self):
        return self.texture
    
class CheeryZookeeper(Zookeepers):
    def __init__(self, position, time, price, time_interval, food_speed, name = 'CheeryZookeeper', size = (Constants.KEEPER_WIDTH, Constants.KEEPER_HEIGHT)):
        Zookeepers.__init__(self, name, size, position, time)
        self.texture = Constants.TEXTURES['SpeedyZookeeper']
        self.price = price
        self.time_interval = time_interval
        self.food_speed = food_speed
    
    def get_texture(self):
        return self.texture
        
# The formation of a rock
class Rock(Formation):
    def __init__(self):
        Formation.__init__(self)
        self.moving = False
        self.texture = Constants.TEXTURES['rock']
    
    def get_texture(self):
        return self.texture
    
# The formation of a food
class Food(Formation):
    def __init__(self, position, time, direction, speed, name = 'food', size = (Constants.FOOD_WIDTH, Constants.FOOD_HEIGHT)):
        Formation.__init__(self, name, size, position, time)
        self.direction = direction
        self.speed = speed
        self.used = False
        self.texture = Constants.TEXTURES['food']
    
    def get_texture(self):
        return self.texture

# The formation of an animal
class Animal(Formation):
    def __init__(self, position, time, speed, name = 'animal', size = (Constants.ANIMAL_WIDTH, Constants.ANIMAL_HEIGHT)):
        Formation.__init__(self, name, size, position, time)
        self.speed = speed
        self.texture = Constants.TEXTURES['animal']
        self.feed_status = False
    
    def get_texture(self):
        return self.texture
    
#    def recur_position(self, graph_dir, total_length = 0):
#        for i in range(len(graph_dir)):
#            pair = graph_dir[i]
#            if pair[0] == 'down':
#                if self.position[0] == pair[1] and pair[2][0] <= self.position[1] < pair[2][1]:
#                    if (self.speed - total_length) > abs(pair[2][1] - self.position[1]):
#                        total_length += pair[2][1] - self.position[1]
#                        self.position = (self.position[0], pair[2][1])
#                        return self.recur_position(self.position, graph_dir[i+1:], total_length)
#                    else:
#                        return (self.position[0], self.position[1] + (self.speed - total_length))
#            elif pair[0] == 'up':
#                if self.position[0] == pair[1] and pair[2][0] >= self.position[1] > pair[2][1]:
#                    if (self.speed - total_length) > abs(pair[2][1] - self.position[1]):
#                        total_length += pair[2][1] - self.position[1]
#                        self.position = (self.positionp[0], pair[2][1])
#                        return self.recur_position(self.position, graph_dir[i+1:], total_length)
#                    else:
#                        return (self.position[0], self.position[1] - (self.speed - total_length))
#            
#            elif pair[0] == 'right':
#                if self.position[1] == pair[1] and pair[2][0] <= self.position[0] < pair[2][1]:
#                    if (self.speed - total_length) > abs(pair[2][1] - self.position[0]):
#                        total_length += pair[2][1] - self.position[0]
#                        self.position = (pair[2][1], self.position[1])
#                        return self.recur_position(self.position, graph_dir[i+1:], total_length)
#                    else:
#                        return (self.position[0] + (self.speed - total_length), self.position[1])
#            
#            else:
#                if self.position[1] == pair[1] and pair[2][0] >= self.position[0] > pair[2][1]:
#                    if (self.speed - total_length) > abs(pair[2][1] - self.position[0]):
#                        total_length += pair[2][1] - self.position[0]
#                        self.position = (pair[2][1], self.position[1])
#                        return self.recur_position(self.position, graph_dir[i+1:], total_length)
#                    else:
#                        return (self.position[0] - (self.speed - total_length), self.position[1])
        
        
################################################################################
################################################################################



if __name__ == '__main__':
   pass
