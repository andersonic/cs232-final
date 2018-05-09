import math
import copy

BEST_MATCHUP = 4
GOOD_MATCHUP = 3
TIE = 2
BAD_MATCHUP = 1
WORST_MATCHUP = 0


class State:
    def __init__(self, my_team, your_team, my_mon_out, your_mon_out):
        self.my_team = my_team
        self.your_team = your_team
        self.my_mon_out = my_mon_out
        self.your_mon_out = your_mon_out

    def make_health_difference_matrix(self):
        health_matrix = [[None for j in range(0, 6)] for i in range(0, 6)]
        for i in range(0, len(health_matrix)):
            for j in range(0, len(health_matrix[i])):
                try:
                    health_matrix[i][j] = self.my_team[i].get_health_percent() - self.your_team[j].get_health_percent()
                except AttributeError:
                    # Unrevealed opponent. It must be at full health.
                    health_matrix[i][j] = self.my_team[i].get_health_percent() - 1

        return health_matrix

    def make_matchup_matrix(self):
        matchup_matrix = [[None for j in range(0, 6)] for i in range(0, 6)]

        for i in range(0, len(matchup_matrix)):
            for j in range(0, len(matchup_matrix[i])):
                try:
                    my_mon = self.my_team[i]
                    your_mon = self.your_team[j]
                    if my_mon.present_health <= 0 and your_mon.present_health <= 0:
                        matchup_matrix[i][j] = TIE
                    elif my_mon.present_health <= 0:
                        matchup_matrix[i][j] = WORST_MATCHUP
                    elif your_mon.present_health<= 0:
                        matchup_matrix[i][j] = BEST_MATCHUP
                    else:
                        matchup_matrix[i][j] = self.get_matchup(my_mon, your_mon)
                except AttributeError:
                    matchup_matrix[i][j] = TIE

        return matchup_matrix

    @staticmethod
    def get_faster(my_mon, your_mon):
        if my_mon.calc_effective_stats[4] > your_mon.calc_effective_stats[4]:
            return my_mon
        elif my_mon.calc_effective_stats[4] < your_mon.calc_effective_stats[4]:
            return your_mon
        else:
            return None

    @staticmethod
    def get_matchup(my_mon, your_mon):
        my_best_damage = 0
        your_best_damage = 0

        if your_mon is None:
            return TIE

        for move in my_mon.moves:
            damage = your_mon.damage_calc(move, my_mon)
            if damage > my_best_damage:
                my_best_damage = damage
        my_best_damage = my_best_damage * 100 / your_mon.total_health

        for move in your_mon.moves:
            damage = my_mon.damage_calc(move, your_mon)
            if damage > your_best_damage:
                your_best_damage = damage
        your_best_damage = your_best_damage * 100 / my_mon.total_health

        faster = None

        if my_mon.calc_effective_stats()[4] > your_mon.calc_effective_stats()[4]:
            faster = my_mon
        elif your_mon.calc_effective_stats()[4] > my_mon.calc_effective_stats()[4]:
            faster = your_mon

        if my_mon is faster and my_best_damage >= 100:
            return BEST_MATCHUP
        elif your_mon is faster and your_best_damage >= 100:
            return WORST_MATCHUP
        elif my_mon is faster and your_best_damage >= 100 and my_best_damage >= 50:
            return BAD_MATCHUP
        elif your_mon is faster and my_best_damage >= 100 and your_best_damage >= 50:
            return GOOD_MATCHUP
        elif my_mon is faster and my_best_damage >= 50:
            return GOOD_MATCHUP
        elif your_mon is faster and your_best_damage >= 50:
            return BAD_MATCHUP
        return TIE

    def get_heuristic(self):
        health_matrix = make_health_difference_matrix()
        matchup_matrix = make_matchup_matrix()

        heuristic_matrix = [[None for j in range(0, 6)] for i in range(0, 6)]

        for i in range(0, len(heuristic_matrix)):
            for j in range(0, len(heuristic_matrix[i])):
                heuristic_matrix[i][j] = (math.e ** health_matrix[i][j]) * matchup_matrix[i][j]

        heuristic = 0
        for i in range(0, len(heuristic_matrix)):
            for j in range(0, len(heuristic_matrix[i])):
                heuristic += heuristic_matrix[i][j]

        return heuristic

    def successor_with_switch(self, successor, myaction, youraction):
        """Handle one or both players switching, damaging moves only"""
        if myaction.switch:
            for mon in self.my_team:
                if mon == myaction:
                    successor.my_mon_out = mon
            assert successor.my_mon_out != self.my_mon_out
            if not youraction.switch:
                successor.my_mon_out.present_health -= \
                    successor.my_mon_out.damage_calc(youraction, successor.your_mon_out)
        if youraction.switch:
            for mon in self.your_team:
                if mon.name == youraction.name:
                    successor.your_mon_out = mon
            assert successor.your_mon_out != self.your_mon_out
            if not myaction.switch:
                successor.your_mon_out.present_health -= \
                    successor.your_mon_out.damage_calc(myaction, successor.my_mon_out)
        return successor

    def successor_both_move(self, successor, myaction, youraction):
        """Handle both players moving"""

        faster = self.get_faster(successor.my_mon_out, successor.your_mon_out)

        if faster is None:
            # Assume you lose the speed tie for now
            faster = successor.your_mon_out

        if successor.your_mon_out is faster:
            successor.my_mon_out.present_health -= \
            successor.my_mon_out.damage_calc(youraction, successor.your_mon_out)

            if successor.my_mon_out.present_health > 0:
                successor.your_mon_out.present_health -= \
                successor.your_mon_out.damage_calc(myaction, successor.my_mon_out)
        else:
            successor.your_mon_out.present_health -= \
            successor.your_mon_out.damage_calc(myaction, successor.my_mon_out)

            if successor.your_mon_out.present_health > 0:
                successor.my_mon_out.present_health -= \
                successor.my_mon_out.damage_calc(youraction, successor.your_mon_out)

    def get_successor(self, myaction, youraction):
        successor = copy.deepcopy(self)

        if myaction.switch or youraction.switch:
            return self.successor_with_switch(successor, myaction, youraction)
        else:
            return self.successor_both_move(successor, myaction, youraction)

    def value(self, depth=0):
        """Returns the value of a state."""
        MAX_DEPTH = 2
        if depth >= MAX_DEPTH:
            return self.get_heuristic()
        else:
            successor_matrix = self.make_successor_matrix()
            probs = self.get_prob(successor_matrix)

            # Multiply each column by its probability. Then sum the rows, and pick the best one
            row_sums = []
            for i in range(0, len(successor_matrix)):
                val = 0
                for j in range(0, len(successor_matrix[i])):
                    val += probs[j] * successor_matrix[i][j].value(depth + 1)[0]
                row_sums.append(val)

            return max(row_sums), row_sums

    @staticmethod
    def get_prob(matrix):
        """Given a 2-D matrix of floats, return a 1-D array proportional to the sums of the columns,
        adjusted to sum to 1."""

        col_sums = []
        total_sum = 0
        # Make CS240 staff cry by iterating on column
        for j in range(0,len(matrix[0])):
            col_sum = 0
            for i in range(0, len(matrix)):
                total_sum += matrix[i][j]
                col_sum += matrix[i][j]
            col_sums.append(col_sum)

        for i in range(0, len(col_sums)):
            col_sums[i] /= total_sum
        return col_sums

    def aux_make_successor_matrix(self, myactions, youractions):
        successor_matrix = []
        for myaction in myactions:
            row = []
            for youraction in youractions:
                row.append(self.get_successor(myaction, youraction))
            successor_matrix.append(row)
        return successor_matrix

    def get_my_actions(self):
        moves = [Action(move) for move in self.my_mon_out.moves]
        switches = [Action(switch, True) for switch in self.my_team if switch is not self.my_mon_out]
        return moves + switches

    def get_your_actions(self):
        moves = [Action(move) for move in self.your_mon_out.moves]
        switches = [Action(switch, True) for switch in self.your_team if switch is not self.your_mon_out]
        return moves + switches

    def make_successor_matrix(self):
        return self.aux_make_successor_matrix(self.get_my_actions(), self.get_your_actions())

    def get_best_action(self):
        move = self.value()
        return self.get_my_actions()[move[1].index(move[0])]

class Action:
    def __init__(self, action, switch=False):
        self.name = action
        self.switch = switch