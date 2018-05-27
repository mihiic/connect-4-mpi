import sys


class Board:
    HUMAN = 2
    CPU = 1
    HEIGHT = 6
    WIDTH = 7

    board = []

    def __init__(self):
        for i in range(self.HEIGHT):
            self.board.append([])
            for j in range(self.WIDTH):
                self.board[i].append(0)

    def from_file(self, file_name):
        with open(file_name, 'r') as file:
            row = 0
            for line in file.readlines():
                line = line.rstrip()
                self.board.append([])
                if line == '':
                    break
                for i, value in enumerate(line.split(' ')):
                    self.board[row][i] = int(value)

                row += 1

    def from_string(self, string):
        cnt = 0
        for i in range(self.HEIGHT):
            for j in range(self.WIDTH):
                self.board[i][j] = string[cnt]
                cnt += 1
        return self

    def to_screen(self):
        for i in range(self.HEIGHT):
            for j in range(self.WIDTH):
                sys.stdout.write(str(self.board[i][j]) + " ")
            sys.stdout.write('\n')

        sys.stdout.flush()

    def move(self, column, player):
        if not self.move_legal(column):
            raise Exception()

        current_row = self.HEIGHT - 1
        for i in range(self.HEIGHT):
            if self.board[i][column] != 0:
                current_row = i - 1
                break

        self.board[current_row][column] = player

    def undo_move(self, column):
        for i in range(self.HEIGHT):
            if self.board[i][column] != 0:
                self.board[i][column] = 0

    def find_winner(self, last_move_col):
        last_move_row = 0
        last_player = 0

        for i in range(self.HEIGHT):
            if self.board[i][last_move_col] != 0:
                last_move_row = i
                last_player = self.board[last_move_row][last_move_col]
                break

        winner = self.check_column(last_move_col, last_player)
        if winner != 0:
            return winner

        winner = self.check_rows(last_move_row, last_player)
        if winner != 0:
            return winner

        winner = self.check_right_diagonal(
            last_move_row, last_move_col, last_player
        )
        if winner != 0:
            return winner

        winner = self.check_left_diagonal(
            last_move_row, last_move_col, last_player
        )
        if winner != 0:
            return winner

        return 0

    def check_left_diagonal(self, last_move_row, last_move_col, last_player):
        start_row = last_move_row
        start_col = last_move_col
        counter = 0

        for j in range(max(self.HEIGHT, self.WIDTH)):
            if last_move_col - j < 0 or last_move_row - j < 0:
                break
            start_row = last_move_row - j
            start_col = last_move_col - j

        for j in range(max(self.HEIGHT, self.WIDTH)):
            if start_col + j >= self.WIDTH or start_row + j >= self.HEIGHT:
                break

            if self.board[start_row + j][start_col + j] == last_player:
                counter += 1
                if counter == 4:
                    return last_player
            else:
                counter = 0

        return 0

    def check_right_diagonal(self, last_move_row, last_move_col, last_player):
        start_row = last_move_row
        start_col = last_move_col
        counter = 0

        for j in range(max(self.HEIGHT, self.WIDTH)):
            if last_move_col + j >= self.WIDTH or last_move_row - j < 0:
                break
            start_row = last_move_row + j
            start_col = last_move_col - j

        for j in range(max(self.HEIGHT, self.WIDTH)):
            if start_col - j < 0 or start_row + j >= self.HEIGHT:
                break

            if self.board[start_row + j][start_col - j] == last_player:
                counter += 1
                if counter == 4:
                    return last_player
            else:
                counter = 0

        return 0

    def check_rows(self, last_move_row, last_player):
        counter = 0
        for j in range(self.WIDTH):
            if self.board[last_move_row][j] == last_player:
                counter += 1
                if counter == 4:
                    return last_player
            else:
                counter = 0
        return 0

    def check_column(self, last_move_col, last_player):
        counter = 0
        for j in range(self.HEIGHT):
            if self.board[j][last_move_col] == last_player:
                counter += 1
                if counter == 4:
                    return last_player
            else:
                counter = 0
        return 0

    def move_legal(self, column):
        if column > 7 or column < 1 or self.board[0][column] != 0:
            return False
        return True

    def to_string(self):
        data = ''
        for i in range(self.HEIGHT):
            for j in range(self.WIDTH):
                data += str(self.board[i][j])
        return data
