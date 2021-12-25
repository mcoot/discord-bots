from dataclasses import dataclass, field
from math import floor
from random import random
from time import sleep
from typing import List
from uuid import uuid4

from pytest import fixture

from commands import (
    ADMINS,
    Author,
    Message,
    is_in_game,
    handle_message,
)
from models import Game, GamePlayer, Player, Queue, QueuePlayer, Session


# Mock discord models so we can invoke tests


@dataclass(frozen=True)
class Author:
    name: str
    id: int = field(default_factory=lambda: floor(random() * 2 ** 32))


@dataclass
class Role:
    name: str
    id: str = field(default_factory=lambda: str(uuid4()).split("-")[0])


@dataclass
class Guild:
    roles: List[Role] = field(default_factory=lambda: [Role("LTpug")])


@dataclass
class Member:
    guild: Guild = Guild()


@dataclass
class Channel:
    pass


@dataclass
class Message:
    author: Member
    content: str
    channel: Channel = Channel()


opsayo = Author("opsayo")
stork = Author("stork")
izza = Author("izza")
lyon = Author("lyon")

ADMINS.add(opsayo)
session = Session()

# handle_message(Message(opsayo, "!commands"))


# Runs around each test
@fixture(autouse=True)
def run_around_tests():
    session.query(QueuePlayer).delete()
    session.query(GamePlayer).delete()
    session.query(Queue).delete()
    session.query(Game).delete()
    session.query(Player).delete()
    session.commit()


def test_is_in_game_with_player_in_game_should_return_true():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(stork, "!add"))

    assert is_in_game(opsayo.id)


def test_is_in_game_with_player_not_in_game_should_return_false():
    assert not is_in_game(opsayo.id)


def test_is_in_game_with_player_in_finished_game_should_return_false():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(stork, "!add"))
    handle_message(Message(stork, "!finishgame loss"))

    assert not is_in_game(opsayo.id)


def test_create_queue_with_odd_size_then_does_not_create_queue():
    handle_message(Message(opsayo, "!createqueue LTgold 5"))

    queues = [q for q in session.query(Queue)]
    assert len(queues) == 0


def test_create_queue_should_create_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))

    queues = [q for q in session.query(Queue)]
    assert len(queues) == 1


def test_remove_queue_should_remove_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))
    handle_message(Message(opsayo, "!removequeue LTpug"))

    queues = [q for q in session.query(Queue)]
    assert len(queues) == 0


def test_remove_queue_with_nonexistent_queue_should_not_throw_exception():
    handle_message(Message(opsayo, "!removequeue LTpug"))

    assert True


def test_add_should_add_player_to_all_queues():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))
    handle_message(Message(opsayo, "!createqueue LTunrated 10"))

    handle_message(Message(opsayo, "!add"))

    for queue_name in ("LTpug", "LTunrated"):
        queue = [q for q in session.query(Queue).filter(Queue.name == queue_name)][0]
        queue_players = [
            qp
            for qp in session.query(QueuePlayer).filter(
                QueuePlayer.player_id == opsayo.id, QueuePlayer.queue_id == queue.id
            )
        ]
        assert len(queue_players) == 1


def test_add_with_multiple_calls_should_not_throw_exception():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))

    handle_message(Message(opsayo, "!add"))
    handle_message(Message(opsayo, "!add"))

    assert True


def test_add_with_queue_named_should_add_player_to_named_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))

    handle_message(Message(opsayo, "!add LTpug"))

    lt_pug_queue = [q for q in session.query(Queue).filter(Queue.name == "LTpug")][0]
    lt_pug_queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.player_id == opsayo.id, QueuePlayer.queue_id == lt_pug_queue.id
        )
    ]
    assert len(lt_pug_queue_players) == 1


def test_add_with_queue_named_should_not_add_player_to_unnamed_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))
    handle_message(Message(opsayo, "!createqueue LTunrated 10"))

    handle_message(Message(opsayo, "!add LTpug"))

    lt_unrated_queue = [
        q for q in session.query(Queue).filter(Queue.name == "LTunrated")
    ][0]
    lt_unrated_queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.player_id == opsayo.id,
            QueuePlayer.queue_id == lt_unrated_queue.id,
        )
    ]
    assert len(lt_unrated_queue_players) == 0


def test_del_should_remove_player_from_all_queues():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))
    handle_message(Message(opsayo, "!createqueue LTunrated 10"))
    handle_message(Message(opsayo, "!add"))

    handle_message(Message(opsayo, "!del"))

    for queue_name in ("LTpug", "LTunrated"):
        queue = [q for q in session.query(Queue).filter(Queue.name == queue_name)][0]
        queue_players = [
            qp
            for qp in session.query(QueuePlayer).filter(
                QueuePlayer.player_id == opsayo.id, QueuePlayer.queue_id == queue.id
            )
        ]
        assert len(queue_players) == 0


def test_del_with_queue_named_should_del_player_from_named_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 10"))
    handle_message(Message(opsayo, "!add LTpug"))

    handle_message(Message(opsayo, "!del LTpug"))

    lt_pug_queue = [q for q in session.query(Queue).filter(Queue.name == "LTpug")][0]
    lt_pug_queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.player_id == opsayo.id, QueuePlayer.queue_id == lt_pug_queue.id
        )
    ]
    assert len(lt_pug_queue_players) == 0


def test_del_with_queue_named_should_not_del_add_player_from_unnamed_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 4"))
    handle_message(Message(opsayo, "!createqueue LTunrated 10"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(opsayo, "!del LTpug"))

    lt_unrated_queue = [
        q for q in session.query(Queue).filter(Queue.name == "LTunrated")
    ][0]
    lt_unrated_queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.player_id == opsayo.id,
            QueuePlayer.queue_id == lt_unrated_queue.id,
        )
    ]
    assert len(lt_unrated_queue_players) == 1


def test_add_with_queue_at_size_should_create_game_and_clear_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 4"))

    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))
    handle_message(Message(stork, "!add"))
    handle_message(Message(izza, "!add"))

    queue = [q for q in session.query(Queue).filter(Queue.name == "LTpug")][0]
    queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.queue_id == queue.id,
        )
    ]
    assert len(queue_players) == 0

    games = [g for g in session.query(Game).filter(Game.queue_id == queue.id)]
    assert len(games) == 1

    game_players = [
        gp for gp in session.query(GamePlayer).filter(GamePlayer.game_id == games[0].id)
    ]
    assert len(game_players) == 4


def test_add_with_player_in_game_should_not_add_to_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))

    handle_message(Message(opsayo, "!add"))

    queue = [q for q in session.query(Queue).filter(Queue.name == "LTpug")][0]
    queue_players = [
        qp
        for qp in session.query(QueuePlayer).filter(
            QueuePlayer.queue_id == queue.id,
        )
    ]
    assert len(queue_players) == 0


def test_status():
    handle_message(Message(opsayo, "!status"))


def test_finish_game_with_win_should_record_win_for_reporting_team():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))

    handle_message(Message(opsayo, "!finishgame win"))

    game_player = [
        gp for gp in session.query(GamePlayer).filter(GamePlayer.player_id == opsayo.id)
    ][0]
    game = [g for g in session.query(Game)][0]
    assert game.winning_team == game_player.team


def test_finish_game_with_loss_should_record_win_for_other_team():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))

    handle_message(Message(opsayo, "!finishgame loss"))

    game_player = [
        gp for gp in session.query(GamePlayer).filter(GamePlayer.player_id == opsayo.id)
    ][0]
    game = [g for g in session.query(Game)][0]
    assert game.winning_team == (game_player.team + 1) % 2


def test_finish_game_with_draw_should_record_draw():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))

    handle_message(Message(opsayo, "!finishgame draw"))

    game = [g for g in session.query(Game)][0]
    assert game.winning_team == -1


def test_finish_game_with_player_not_in_game_should_not_finish_game():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))

    handle_message(Message(stork, "!finishgame loss"))

    game = [g for g in session.query(Game)][0]
    assert game.winning_team is None


def test_add_with_player_after_finish_game_should_be_added_to_queue():
    handle_message(Message(opsayo, "!createqueue LTpug 2"))
    handle_message(Message(opsayo, "!add"))
    handle_message(Message(lyon, "!add"))
    handle_message(Message(opsayo, "!finishgame win"))

    handle_message(Message(opsayo, "!add"))

    queue_players = [qp for qp in session.query(QueuePlayer)]
    assert len(queue_players) == 1


def test_add_admin_should_add_player_to_admins():
    # handle_message(Message(opsayo, "!addadmin lyon"))
    pass


def test_add_admin_with_non_admin_should_not_add_player_to_admins():
    # handle_message(Message(izza, "!addadmin stork"))
    pass


def test_remove_admin_should_remove_player_from_admins():
    # handle_message(Message(opsayo, "!addadmin lyon"))
    # handle_message(Message(opsayo, "!removeadmin lyon"))
    pass


def test_remove_admin_with_self_should_not_remove_player_from_admins():
    # handle_message(Message(opsayo, "!removeadmin opsayo"))
    pass


def test_remove_admin_with_non_admin_should_not_remove_player_from_admins():
    # handle_message(Message(izza, "!addadmin stork"))
    pass


# handle_message(Message(stork, "!status"))
# handle_message(Message(stork, "!sub"))
# handle_message(Message(izza, "!sub lyon"))
# handle_message(Message(stork, "!sub opsayo"))
# handle_message(Message(stork, "!sub izza"))
# handle_message(Message(stork, "!status"))

# handle_message(Message(opsayo, "!cancelgame"))
# handle_message(Message(opsayo, "!status"))
# assert len(GAMES["LTpug"]) == 1
# handle_message(Message(lyon, "!cancelgame"))
# handle_message(Message(opsayo, "!status"))
# assert len(GAMES["LTpug"]) == 0
# handle_message(Message(lyon, "!add LTpug"))

# # Re-add timer triggers here
# handle_message(Message(stork, "!add LTpug"))
# assert len(GAMES["LTpug"]) == 0
# sleep(RE_ADD_DELAY)
# handle_message(Message(stork, "!add LTpug"))
# assert len(GAMES["LTpug"]) == 1

# handle_message(Message(stork, "!cancelgame " + GAMES["LTpug"][0].id))
# assert len(GAMES["LTpug"]) == 1
# handle_message(Message(opsayo, "!cancelgame " + GAMES["LTpug"][0].id))
# assert len(GAMES["LTpug"]) == 0
# handle_message(Message(opsayo, "!status"))

# handle_message(Message(opsayo, "!ban lyon"))
# assert len(BANNED_PLAYERS) == 1
# handle_message(Message(opsayo, "!ban lyon"))
# assert len(BANNED_PLAYERS) == 1
# handle_message(Message(izza, "!ban opsayo"))
# assert len(BANNED_PLAYERS) == 1
# handle_message(Message(opsayo, "!listbans"))

# handle_message(Message(opsayo, "!unban lyon"))
# assert len(BANNED_PLAYERS) == 0
# handle_message(Message(opsayo, "!unban lyon"))
# handle_message(Message(izza, "!unban opsayo"))
# handle_message(Message(opsayo, "!listbans"))

# handle_message(Message(opsayo, "!coinflip"))
# handle_message(Message(opsayo, "!setcommandprefix"))
# handle_message(Message(opsayo, "!setcommandprefix #"))
# handle_message(Message(opsayo, "#coinflip"))
# handle_message(Message(opsayo, "#setcommandprefix !"))
# handle_message(Message(opsayo, "!coinflip"))

# handle_message(Message(opsayo, "!setadddelay"))
# handle_message(Message(opsayo, "!setadddelay 1"))
# sleep(1)

# handle_message(Message(opsayo, "!add LTpug"))
# handle_message(Message(stork, "!add LTpug"))
# handle_message(Message(opsayo, "!finishgame win"))
# handle_message(Message(opsayo, "!add LTpug"))
# assert len(QUEUES["LTpug"].players) == 0
