import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.game import check_save_file

if __name__ == "__main__":
    from src.game import start_new_game, main_menu

    if not check_save_file():
        start_new_game()
    else:
        main_menu()
