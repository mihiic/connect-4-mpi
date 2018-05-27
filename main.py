import copy
import os
import sys
import time
from mpi4py import MPI
from board import Board
from message import Message


class Program:
    def __init__(self):
        self.max_depth = 8
        self.file_name = 'board.txt'
        self.comm = MPI.COMM_WORLD
        self.rank = self.comm.Get_rank()
        self.size = self.comm.Get_size()
        self.board = None
        self.tasks = {}
        self.results = 0

    def main(self):
        if self.rank == 0:
            self.master()
        else:
            self.worker()

        sys.stdout.flush()

    def worker(self):
        done = False
        self.board = Board()

        while not done:
            recv_msg = self.comm.recv(source=0, tag=0)
            if not self.process_master_msgs(recv_msg):
                break

            while True:
                req = Message({
                    'msg_type': 'request',
                    'process_id': self.rank
                })
                self.comm.send(req, 0, 0)

                task = self.comm.recv(source=0, tag=0)

                if task.msg_type == 'end':
                    done = True
                    break

                try:
                    self.board.move(task.move_cpu, Board.CPU)
                except:
                    pass

                if self.board.find_winner(task.move_cpu) == Board.CPU:
                    result = Message({
                        'msg_type': 'result',
                        'move_cpu': task.move_cpu,
                        'move_player': task.move_player,
                        'evaluation': 1,
                        'process_id': self.rank
                    })

                    self.comm.send(result, 0, 0)
                    self.board.undo_move(task.move_cpu)
                    sys.stdout.write('Winner: CPU')
                    sys.stdout.flush()

                try:
                    self.board.move(task.move_player, Board.HUMAN)
                except:
                    pass

                if self.board.find_winner(task.move_player) == Board.HUMAN:
                    result = Message({
                        'msg_type': 'result',
                        'move_cpu': task.move_cpu,
                        'move_player': task.move_player,
                        'evaluation': -1,
                        'process_id': self.rank
                    })

                    self.comm.send(result, 0, 0)
                    self.board.undo_move(task.move_cpu)
                    self.board.undo_move(task.move_player)
                    sys.stdout.write('Winner: Player')
                    sys.stdout.flush()

                result = Message({
                    'msg_type': 'result',
                    'move_cpu': task.move_cpu,
                    'move_player': task.move_player,
                    'process_id': self.rank
                })
                result.evaluation = self.evaluate(self.board, Board.HUMAN, task.move_player, self.max_depth - 3)
                self.board.undo_move(task.move_player)
                self.board.undo_move(task.move_cpu)
                self.comm.send(result, 0, 0)

    def evaluate(self, _board, last_player, column, depth):
        result_sum = 0
        move_cnt = 0
        all_bad = True
        all_good = True

        board = copy.deepcopy(_board)

        winner = board.find_winner(column)
        if winner == Board.CPU:
            return 1
        if winner == Board.HUMAN:
            return -1

        if depth == 0:
            return 0

        if last_player == Board.HUMAN:
            next_player = Board.CPU
        else:
            next_player = Board.HUMAN

        for i in range(Board.WIDTH):
            if board.move_legal(i):
                move_cnt += 1
                board.move(i, next_player)
                result = self.evaluate(board, next_player, i, depth - 1)
                board.undo_move(i)

                if result == 1 and next_player == Board.CPU:
                    return 1
                if result == -1 and next_player == Board.HUMAN:
                    return -1
                if result > -1:
                    all_bad = False
                if result != 1:
                    all_good = False

                result_sum += result

        if all_good:
            return 1
        if all_bad:
            return -1

        return result_sum / float(move_cnt)

    def process_master_msgs(self, recv_msg):
        if recv_msg.msg_type == 'end':
            return False

        if recv_msg.msg_type == 'table':
            self.board = self.board.from_string(recv_msg.board)

        return True

    def master(self):
        start = time.time()
        self.board = Board()
        self.board.from_file(self.file_name)
        self.board.to_screen()

        if self.check_winner():
            sys.stdout.flush()
            return

        msg = Message({
            'msg_type': 'table',
            'board': self.board.to_string()
        })

        self.notify_workers(msg)
        self.process_game()

        sys.stdout.write('Done! Received {} results.\n\n'.format(self.results))
        sys.stdout.flush()

        end_msg = Message({
            'msg_type': 'end'
        })
        self.notify_workers(end_msg)
        best_column, best = self.get_best_results()

        sys.stdout.write('\nBest column: {} , with value: {}'.format(best_column, best))
        sys.stdout.flush()
        sys.stdout.write('Time elapsed: {}'.format(time.time() - start))
        sys.stdout.flush()

    def notify_workers(self, msg):
        for i in range(1, self.size):
            self.comm.send(msg, dest=i, tag=0)

    def process_game(self):
        done = False
        while not done:
            received_msg = self.comm.recv()
            sys.stdout.write('Received: {} from {}\n'.format(received_msg.msg_type, received_msg.process_id))
            sys.stdout.flush()

            if received_msg.msg_type == 'request':
                try:
                    task = self.fetch_tasks()
                    task_msg = Message({
                        'msg_type': 'task',
                        'move_cpu': task[0],
                        'move_player': task[1]
                    })

                    self.comm.send(task_msg, dest=received_msg.process_id)
                except:
                    # done = True
                    pass

            elif received_msg.msg_type == 'result':
                task_tag = '{},{}'.format(
                    received_msg.move_cpu, received_msg.move_player
                )
                self.tasks[task_tag] = received_msg.evaluation

                if self.results == Board.WIDTH * Board.HEIGHT:
                    done = True

    def get_best_results(self):
        column_results = []
        for i in range(Board.WIDTH):
            column_results.append(0)
            for j in range(Board.HEIGHT):
                tag = '{},{}'.format(i, j)
                column_results[i] += self.tasks[tag] / float(Board.WIDTH)

        number = 0
        for n in column_results:
            sys.stdout.write("{}: {}".format(number, n))
            sys.stdout.flush()
            number += 1

        best = max(column_results)
        best_column = column_results.index(best)
        return best_column, best

    def fetch_tasks(self):
        for i in range(self.board.WIDTH):
            for j in range(self.board.WIDTH):
                if not '{},{}'.format(i, j) in self.tasks.keys():
                    self.tasks['{},{}'.format(i, j)] = 0
                    return [i, j]

        sys.stdout.write('\nFailed at {}\n'.format(self.tasks is None))
        sys.stdout.flush()
        raise Exception()

    def check_winner(self):
        for i in range(Board.WIDTH):
            winner = self.board.find_winner(i)
            if winner != 0:
                self.board.to_screen()

                if winner == 1:
                    sys.stdout.write('Pobjednik je: CPU')
                    sys.stdout.flush()
                else:
                    sys.stdout.write('Pobjednik je: HUMAN')
                    sys.stdout.flush()

                sys.stdout.flush()
                return True
        return False


if __name__ == '__main__':
    program = Program()
    program.main()
