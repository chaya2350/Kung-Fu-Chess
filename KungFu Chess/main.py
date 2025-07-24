
import logging
from GameFactory import create_game
from Img import

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    game = create_game("./pieces", Img.)
    game.run()

