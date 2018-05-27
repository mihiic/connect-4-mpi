class Message:
    def __init__(self, data):
        self.msg_type = data.get('msg_type', None)
        self.board = data.get('board', None)
        self.evaluation = data.get('evaluation', None)
        self.move_player = data.get('move_player', None)
        self.move_cpu = data.get('move_cpu', None)
        self.process_id = data.get('process_id', None)
